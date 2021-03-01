var Dropbox = require('dropbox');

function dropboxAuth() {
  // You need to register your app on https://www.dropbox.com/developers/apps
  // and paste client id below
  var dbx = new Dropbox({ clientId: window.DROPBOX_APP_KEY });

  var redirectUrl = `${location.origin}/account/dropbox_auth_callback`;

  // Add url to Redirect URIs in your app https://www.dropbox.com/developers/apps
  var authUrl = dbx.getAuthenticationUrl(redirectUrl);
  location.href = authUrl;
}

function getFolders(path, token) {
  var dbx = new Dropbox({ accessToken: token });
  return dbx.filesListFolder({ path });
}

/* eslint-disable */
module.exports = {
  getFolders,
  dropboxAuth
}
