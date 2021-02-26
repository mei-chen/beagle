import _ from 'lodash';

import React from 'react';
import humanizeUrl from 'humanize-url';
import normalizeUrl from 'normalize-url';

import { NoData } from './NoData';
import Widget from './Widget';
import Spinner from './Spinner';
import replaceLineBreaks from 'utils/replaceLineBreak';

require('./styles/ExtRefsWidget.scss');


const ExtRef = React.createClass({
  clickOnURL(e) {
    e.stopPropagation();
  },

  render() {
    var data = this.props.data;

    var inner;
    if (data.reftype === 'URL' || data.reftype === 'Domain') {
      var url = replaceLineBreaks(data.form, '');
      inner = <a target="_blank" href={normalizeUrl(url)} onClick={this.clickOnURL}>{humanizeUrl(url)}</a>;
    } else if (data.reftype === 'Email') {
      var email = data.form;
      inner = <a target="_blank" href={'mailto:' + email} onClick={this.clickOnURL}>{email}</a>;
    } else {
      inner = '(' + data.reftype + ') ' + replaceLineBreaks(data.form, ' ');
    }
    return <li>{inner}</li>;
  }
});


const ExtRefsWidget = React.createClass({

  render() {
    var widgetContent;
    const isLoaded = this.props.analysis && this.props.analysis.sentences.length !== 0;
    if (!isLoaded) {
      widgetContent = <Spinner/>;
    } else {
      var allSentences = this.props.analysis.sentences;
      // get the external_refs list out of every sentence, and remove the empty lists
      var flattenedExtRefs = _.flatten(_.map(allSentences, 'external_refs'));
      var allExtRefs = _.filter(flattenedExtRefs, _.isObject);

      if (allExtRefs.length === 0) {
        widgetContent = <NoData />;
      } else {
        // given a external reference object, return a key.
        // the key is sorted on and used as identity for uniqueness filter
        var refKey = function(ref) {
          return '' + normalizeUrl(ref.form);
        }

        // sort the ext refs by form
        var sortedExtRefs = _.sortBy(allExtRefs, refKey);
        // remove the ext refs that are not unique
        var uniqueExtRefs = _.uniq(sortedExtRefs, refKey);

        var listItems = uniqueExtRefs.map((ref, idx) =>
          <ExtRef data={ref} key={idx}/>
        );

        widgetContent = <ul id="external-refs">{listItems}</ul>;
      }
    }
    return (
      <Widget title="External References" className="references">
        {widgetContent}
      </Widget>
    );
  }

});


module.exports = ExtRefsWidget;
