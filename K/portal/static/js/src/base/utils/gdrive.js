var apiKey = 'AIzaSyAb_m3H2ckI6r69wqbUtGjJhkBpjEzBY3o';
var clientId = '90167931961-7scgksjtvv9g9i9duf978k4u3nq7bb0b';
var scope = ['https://www.googleapis.com/auth/drive'];
var pickerApiLoaded = false;

function openPicker(callback) {
  // Check if the user has already authenticated
  var showPickerWithCallback = function() {
    showPicker(callback);
  }
  var token = gapi.auth.getToken();
  if (token) {
    showPicker(callback);
  } else {
    // The user has not yet authenticated with Google
    // We need to do the authentication before displaying the Drive picker.
    onAuthApiLoad(false, showPickerWithCallback);
  }
}

export function openFolderPicker(callback) {
  // Check if the user has already authenticated
  var showPickerWithCallback = function() {
    showFolderPicker(callback);
  }
  var token = gapi.auth.getToken();
  if (token) {
    showFolderPicker(callback);
  } else {
    // The user has not yet authenticated with Google
    // We need to do the authentication before displaying the Drive picker.
    onAuthApiLoad(false, showPickerWithCallback);
  }
}

// Use the API Loader script to load google.picker and gapi.auth.
function onApiLoad() {
  gapi.client.setApiKey(apiKey);
  gapi.client.load('drive', 'v2',  driveAPILoad );
  google.load('picker', '1', {'callback': onPickerApiLoad});
}

function driveAPILoad() {
  onAuthApiLoad(true);
}


function onAuthApiLoad(immediate, callback) {
  gapi.auth.authorize({
    'client_id': clientId,
    'scope': scope,
    'immediate': immediate
  }, callback);
}

function onPickerApiLoad() {
  pickerApiLoaded = true;
}

// Create and render a Picker object for picking user Photos.
function showPicker(callback) {
  var accessToken = gapi.auth.getToken().access_token;
  var wrappedCallback = function(data) {
    pickerCallback(data, callback);
  }

  if (pickerApiLoaded && accessToken) {
    var picker = new google.picker.PickerBuilder().
      enableFeature(google.picker.Feature.MULTISELECT_ENABLED).
      addView(new google.picker.DocsView().
        setIncludeFolders(true).        //Include Folders
        setSelectFolderEnabled(false).
        setMode(google.picker.DocsViewMode.LIST).
        setMimeTypes("text/plain,application/msword,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.google-apps.document")).
      setOAuthToken(accessToken).
      setDeveloperKey(apiKey).
      setCallback(wrappedCallback).
      build();
    picker.setVisible(true);
  }
}

// Create and render a Picker object for picking user Folders.
function showFolderPicker(callback) {
  var accessToken = gapi.auth.getToken().access_token;
  var wrappedCallback = function(data) {
    folderPickerCallback(data, callback);
  }

  if (pickerApiLoaded && accessToken) {
    var docsView = new google.picker.DocsView()
              .setIncludeFolders(true)
              .setMimeTypes('application/vnd.google-apps.folder')
              .setSelectFolderEnabled(true);

            var picker = new google.picker.PickerBuilder()
              .addView(docsView)
              .setOAuthToken(accessToken)
              .setDeveloperKey(apiKey)
              .setCallback(wrappedCallback)
              .build();

            picker.setVisible(true);
  }
}

// A simple callback implementation.
function pickerCallback(data, callback) {
  if (data[google.picker.Response.ACTION] == google.picker.Action.PICKED) {
    var accessToken = gapi.auth.getToken().access_token;
    var docs = data[google.picker.Response.DOCUMENTS];
    docs.map((v) => {
      gapi.client.load('drive', 'v2', function() {
        makeRequest(v.id, callback, accessToken);
      });
    });
    // var name = doc[google.picker.Document.NAME]
    var url,request;
  }
}

function folderPickerCallback(data, callback) {
  if (data[google.picker.Response.ACTION] == google.picker.Action.PICKED) {
    callback(data.docs[0]);
  }
}

function makeRequest(fileId, setGoogleFileState, accessToken) {
  var request = gapi.client.drive.files.get({
    'fileId': fileId
  });

  request.execute(function(resp) {

    console.log('response: ',resp);
    var mimeType = resp.mimeType;

    if ( mimeType === 'application/vnd.google-apps.document') { //Check if GoogleDoc
      isGoogleDoc(resp, accessToken, setGoogleFileState);
    } else {
      isTxt(resp, accessToken, setGoogleFileState);
    }


    //setGoogleFileState(resp.title, url, accessToken);
  });
}

function isTxt(resp, accessToken, setGoogleFileState) {
    setGoogleFileState(resp.title, resp.downloadUrl, accessToken, 'gdrive');
}

function isGoogleDoc(resp, accessToken, setGoogleFileState) {
    var docx = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    var url = resp.exportLinks[docx];
    setGoogleFileState(resp.title, url, accessToken, 'gdrive');
}
