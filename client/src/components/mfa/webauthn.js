import axios from 'axios';
import base64js from 'base64-js';

export async function webauthnRegisterBegin(user={}) {
  let payload = user
  // Get PublicKeyCredentialRequestOptions for this user from the server
  const credentialCreateOptionsFromServer = await axios.get('/mfa/webauthn/register', { params: payload })
  // Convert certain members of the PublicKeyCredentialCreateOptions into byte arrays as expected by the spec.
  const publicKeyCredentialCreateOptions = transformCredentialCreateOptions(credentialCreateOptionsFromServer.data)
  // Request the authenticator(s) to create a new credential keypair.
  const credential = await navigator.credentials.create({ publicKey: publicKeyCredentialCreateOptions })
  // Encode the byte arrays in the credential into strings
  const newAssertionForServer = transformNewAssertionForServer(credential)
  return newAssertionForServer
}

export async function webauthnRegisterValidate(credential, user={}) {
  // Posts the new credential data to the server for validation and storage.
  const payload = { ...user, credential }
  await axios.post('/mfa/webauthn/register', payload)
}

export async function webauthnRegisterFinish(credential, user={}) {
  // Posts the new credential data to the server for validation and storage.
  const payload = {...user, credential, store: true}
  return await axios.post('/mfa/webauthn/register', payload)
}

export async function webauthnLogin(PublicKeyCredentialRequestOptions) {
  // Convert certain members of the PublicKeyCredentialRequestOptions into byte arrays as expected by the spec.
  const transformedCredentialRequestOptions = transformCredentialRequestOptions(JSON.parse(PublicKeyCredentialRequestOptions));
  // Request the authenticator to create an assertion signature using the credential private key
  const assertion = await navigator.credentials.get({ publicKey: transformedCredentialRequestOptions });
  // Encode the byte arrays contained in the assertion data as strings for posting to the server
  return transformAssertionForServer(assertion);
}

/* ---------------- */
/* INTERNAL METHODS */
/* ---------------- */
// Convert certain members of the PublicKeyCredentialCreateOptions into byte arrays as expected by the spec
function transformCredentialCreateOptions(credentialCreateOptionsFromServer) {
  let { challenge, user } = credentialCreateOptionsFromServer
  user.id = Uint8Array.from(
    atob(credentialCreateOptionsFromServer.user.id.replace(/_/g, "/").replace(/-/g, "+")),
    c => c.charCodeAt(0)
  )
  challenge = Uint8Array.from(
    atob(credentialCreateOptionsFromServer.challenge.replace(/_/g, "/").replace(/-/g, "+")),
    c => c.charCodeAt(0)
  )
  const transformedCredentialCreateOptions = Object.assign({}, credentialCreateOptionsFromServer, { challenge, user })
  return transformedCredentialCreateOptions
}

// Transforms the binary data in the credential into base64 strings
function transformNewAssertionForServer(newAssertion) {
  return {
    id: newAssertion.id,
    rawId: b64enc(new Uint8Array(newAssertion.rawId)),
    type: newAssertion.type,
    response: {
      attestationObject: b64enc(new Uint8Array(newAssertion.response.attestationObject)),
      clientDataJSON: b64enc(new Uint8Array(newAssertion.response.clientDataJSON))
    },
    registrationClientExtensions: JSON.stringify(newAssertion.getClientExtensionResults())
  }
}

const transformAssertionForServer = (newAssertion) => {
  return {
    id: newAssertion.id,
    rawId: b64enc(new Uint8Array(newAssertion.rawId)),
    response: {
      authenticatorData: b64RawEnc(new Uint8Array(newAssertion.response.authenticatorData)),
      clientDataJSON: b64RawEnc(new Uint8Array(newAssertion.response.clientDataJSON)),
      signature: b64RawEnc(new Uint8Array(newAssertion.response.signature)),
      userHandle: b64RawEnc(new Uint8Array(newAssertion.response.userHandle)),
    },
    type: newAssertion.type,
    clientExtensionResults: newAssertion.getClientExtensionResults()
  }
}

function transformCredentialRequestOptions(credentialRequestOptionsFromServer) {
  let { challenge, allowCredentials } = credentialRequestOptionsFromServer;
  challenge = Uint8Array.from(
    atob(challenge.replace(/_/g, "/").replace(/-/g, "+")), c => c.charCodeAt(0)
  );
  allowCredentials = allowCredentials.map(credentialDescriptor => {
    let { id } = credentialDescriptor;
    id = id.replace(/_/g, "/").replace(/-/g, "+");
    id = Uint8Array.from(atob(id), c => c.charCodeAt(0));
    return Object.assign({}, credentialDescriptor, { id });
  });
  const transformedCredentialRequestOptions = Object.assign(
    {},
    credentialRequestOptionsFromServer,
    { challenge, allowCredentials }
  );
  return transformedCredentialRequestOptions;
}

function b64enc(buf) {
  return base64js.fromByteArray(buf).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "")
}

function b64RawEnc(buf) {
  return base64js.fromByteArray(buf)
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
}
