// Run only through the Firestore emulator; never use production credentials.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const dependency = process.env.NOTICE_FIREBASE_TEST_MODULES;
const load = dependency ? createRequire(path.resolve(dependency, '../package.json')) : require;
const { initializeTestEnvironment, assertSucceeds, assertFails } = load('@firebase/rules-unit-testing');
const { doc, setDoc, getDoc, getDocs, collection, updateDoc, deleteDoc, serverTimestamp, query, orderBy, limit } = load('firebase/firestore');
(async () => {
  assert(process.env.FIRESTORE_EMULATOR_HOST, 'Run through firebase emulators:exec');
  const env = await initializeTestEnvironment({ projectId: 'demo-high-church', firestore: {rules:fs.readFileSync('firebase/firestore.rules', 'utf8')} });
  try {
    await env.withSecurityRulesDisabled(async ctx => {
      await setDoc(doc(ctx.firestore(), 'members/alice'), {enabled:true});
      await setDoc(doc(ctx.firestore(), 'members/bob'), {enabled:true});
      await setDoc(doc(ctx.firestore(), 'members/revoked'), {enabled:false});
    });
    const alice=env.authenticatedContext('alice').firestore(), bob=env.authenticatedContext('bob').firestore();
    const unknown=env.authenticatedContext('unknown').firestore(), revoked=env.authenticatedContext('revoked').firestore();
    const guest=env.unauthenticatedContext().firestore();
    const snapshot={title:'Synthetic youth notice',weekDate:'2026-11-01',content:JSON.stringify({services:[],notices:[{title:'Youth',body:'Synthetic notice',column:'right'}]}),createdBy:'alice',createdAt:serverTimestamp()};
    await assertSucceeds(setDoc(doc(alice,'noticeArchive/week-one'),snapshot));
    await assertSucceeds(getDoc(doc(bob,'noticeArchive/week-one')));
    await assertSucceeds(getDocs(query(collection(bob,'noticeArchive'),orderBy('createdAt','desc'),orderBy('__name__','desc'),limit(50))));
    for(const client of [guest,unknown,revoked]) {
      await assertFails(getDoc(doc(client,'noticeArchive/week-one')));
      await assertFails(getDocs(collection(client,'noticeArchive')));
      await assertFails(setDoc(doc(client,'noticeArchive/forbidden'),snapshot));
    }
    await assertSucceeds(getDoc(doc(alice,'members/alice')));
    await assertFails(getDoc(doc(alice,'members/bob')));
    await assertFails(getDocs(collection(alice,'members')));
    await assertFails(setDoc(doc(unknown,'members/unknown'),{enabled:true}));
    await assertFails(updateDoc(doc(alice,'members/alice'),{enabled:false}));
    await assertFails(setDoc(doc(alice,'noticeArchive/forged-user'),{...snapshot,createdBy:'bob'}));
    await assertFails(setDoc(doc(alice,'noticeArchive/forged-date'),{...snapshot,createdAt:new Date(0)}));
    await assertFails(setDoc(doc(alice,'noticeArchive/extra-fields'),{...snapshot,emailInput:'Must not be shared'}));
    await assertFails(setDoc(doc(alice,'noticeArchive/oversized'),{...snapshot,content:'x'.repeat(100001)}));
    await assertFails(setDoc(doc(alice,'noticeArchive/missing-title'),{...snapshot,title:''}));
    await assertFails(updateDoc(doc(alice,'noticeArchive/week-one'),{title:'Overwrite'}));
    await assertFails(deleteDoc(doc(alice,'noticeArchive/week-one')));
    await env.withSecurityRulesDisabled(ctx=>updateDoc(doc(ctx.firestore(),'members/alice'),{enabled:false}));
    await assertFails(getDoc(doc(alice,'noticeArchive/week-one')));
    await assertFails(setDoc(doc(alice,'noticeArchive/after-revocation'),snapshot));
    console.log('PASS Firestore rules: cross-member reads, approved publication, anonymous/unapproved/revoked denial, protected membership, immutable snapshots, field/size/timestamp/author validation and immediate revocation');
  } finally { await env.cleanup(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
