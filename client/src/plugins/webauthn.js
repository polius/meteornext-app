var axios = require('axios')
var base64js = require('base64-js')

export async function webauthnRegister() {
  // Get PublicKeyCredentialRequestOptions for this user from the server
  let credentialCreateOptionsFromServer;
  try {
    const payload = { host: window.location.host }
    credentialCreateOptionsFromServer = await axios.post('/mfa/webauthn/register', payload)
  } catch (error) {
    throw {error: error.response}
  }
  // Convert certain members of the PublicKeyCredentialCreateOptions into byte arrays as expected by the spec.
  const publicKeyCredentialCreateOptions = transformCredentialCreateOptions(credentialCreateOptionsFromServer.data)
  // Request the authenticator(s) to create a new credential keypair.
  let credential;
  try {
    credential = await navigator.credentials.create({ publicKey: publicKeyCredentialCreateOptions })
  } catch(error) {
    throw {error}
  }
  // Encode the byte arrays in the credential into strings
  const newAssertionForServer = transformNewAssertionForServer(credential)
  // Posts the new credential data to the server for validation and storage.
  try {
    const payload = { host: window.location.host, credential: newAssertionForServer }
    await axios.post('/mfa/webauthn/verify', payload)
  } catch (error) {
    throw {error: error.response}
  }
}

export async function webauthnLogin() {

}

/* ---------------- */
/* INTERNAL METHODS */
/* ---------------- */
// Convert certain members of the PublicKeyCredentialCreateOptions into byte arrays as expected by the spec
function transformCredentialCreateOptions(credentialCreateOptionsFromServer) {
  let {challenge, user} = credentialCreateOptionsFromServer
  user.id = Uint8Array.from(
    atob(credentialCreateOptionsFromServer.user.id.replace(/_/g, "/").replace(/-/g, "+")), 
    c => c.charCodeAt(0)
  )
  challenge = Uint8Array.from(
    atob(credentialCreateOptionsFromServer.challenge.replace(/_/g, "/").replace(/-/g, "+")),
    c => c.charCodeAt(0)
  )
  const transformedCredentialCreateOptions = Object.assign({}, credentialCreateOptionsFromServer, {challenge, user})
  return transformedCredentialCreateOptions
}

// Transforms the binary data in the credential into base64 strings
function transformNewAssertionForServer(newAssertion) {
  const attObj = new Uint8Array(newAssertion.response.attestationObject)
  const clientDataJSON = new Uint8Array(newAssertion.response.clientDataJSON)
  const rawId = new Uint8Array(newAssertion.rawId)
  const registrationClientExtensions = newAssertion.getClientExtensionResults()
  return {
    id: newAssertion.id,
    rawId: b64enc(rawId),
    type: newAssertion.type,
    attObj: b64enc(attObj),
    clientData: b64enc(clientDataJSON),
    registrationClientExtensions: JSON.stringify(registrationClientExtensions)
  }
}
function b64enc(buf) {
  return base64js.fromByteArray(buf).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "")
}