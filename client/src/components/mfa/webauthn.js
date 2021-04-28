var axios = require('axios')
var base64js = require('base64-js')

export async function webauthnRegister(user='') {
  let payload = (user == '') ? { host: window.location.host } : { user, host: window.location.host }
  // Get PublicKeyCredentialRequestOptions for this user from the server
  let credentialCreateOptionsFromServer = await axios.get('/mfa/webauthn', { params: payload })
  // Convert certain members of the PublicKeyCredentialCreateOptions into byte arrays as expected by the spec.
  const publicKeyCredentialCreateOptions = transformCredentialCreateOptions(credentialCreateOptionsFromServer.data)
  // Request the authenticator(s) to create a new credential keypair.
  let credential = await navigator.credentials.create({ publicKey: publicKeyCredentialCreateOptions })
  // Encode the byte arrays in the credential into strings
  const newAssertionForServer = transformNewAssertionForServer(credential)
  // Posts the new credential data to the server for validation and storage.
  payload = {...payload, credential: newAssertionForServer }
  await axios.post('/mfa/webauthn', payload)
  return newAssertionForServer
}

export async function webauthnStore(newAssertionForServer, user='') {
  // Posts the new credential data to the server for validation and storage.
  let payload = { host: window.location.host, credential: newAssertionForServer, store: true }
  payload = (user == '') ? payload : {...payload, user}
  return await axios.post('/mfa/webauthn', payload)
}

export async function webauthnLogin() {

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