import React from 'react';
import { render } from 'react-dom';
import { Provider } from 'react-redux';
import { Router, Route, hashHistory, IndexRedirect } from 'react-router';

import configureStore from 'store';
import Root from 'root';
import LocalFolder from 'LocalFolder';
import OnlineFolder from 'OnlineFolder';
import ProjectManagement from 'ProjectManagement';
import BatchManagement from 'BatchManagement';
import IdentifiableInformation from 'IdentifiableInformation'
//import OCR from 'OCR'; //Remove for now
import FormatConverting from 'FormatConverting';
import CleanupDocument from 'CleanupDocument';
import SentenceSplitting from 'SentenceSplitting';
import CleanupSentences from 'CleanupSentences';
import Sentences from 'SentenceSearch'
import KeyWords from 'KeyWords';
import RegEx from 'RegEx';
import SentencesObfuscation from 'SentencesObfuscation';
import Settings from 'Settings';
import Sidebar from 'base/components/Sidebar';

const store = configureStore();

const router = (
  <Router history={hashHistory}>
    <Route path="/" component={Root}>
      <IndexRedirect to="/local-folder" />
      <Route path="local-folder" component={LocalFolder}/>
      <Route path="online-folder" component={OnlineFolder}/>
      <Route path="project-management" component={ProjectManagement}/>
      <Route path="batch-management" component={BatchManagement}/>
      <Route path="identifiable-information" component={IdentifiableInformation}/>
      {/* //<Route path="ocr" component={OCR}/>// Remove for now */}
      <Route path="format-converting" component={FormatConverting}/>
      <Route path="cleanup-document" component={CleanupDocument}/>
      <Route path="sentence-splitting" component={SentenceSplitting}/>
      <Route path="cleanup-sentences" component={CleanupSentences}/>
      <Route path="sentences" component={Sentences}/>
      <Route path="key-words" component={KeyWords}/>
      <Route path="reg-ex" component={RegEx}/>
      <Route path="sentences-obfuscation" component={SentencesObfuscation}/>
      <Route path="settings" component={Settings}/>
    </Route>
  </Router>
);

render(
  <Provider store={store}>
    <Sidebar>
      { router }
    </Sidebar>
  </Provider>,

  document.getElementById('app')
);
