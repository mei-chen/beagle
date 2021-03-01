import {
  convertFromRaw,
  convertToRaw,
  CompositeDecorator,
  Editor,
  EditorState
} from 'draft-js';
import React, { Component } from 'react';
import _ from 'lodash';

// App
import LBR_MARKER from 'utils/LINEBREAK_MARKER';
import NBR_MARKER from 'utils/NUMBERING_MARKER';

require('./styles/CustomEditor.scss');

const ILVL_LOCAL_MARKER = /(?:__\/ILVL\/([0-9]+)\/__)/;
const ILVL_MARKER = /(?:__\/ILVL\/([0-9]+)\/__)(?:.*)/g;
const ilvlRegExp = new RegExp(ILVL_MARKER);
const ilvlRegExpLocal = new RegExp(ILVL_LOCAL_MARKER);
const nbrRegExp = new RegExp(NBR_MARKER);


const getEntityStrategy = (mutability) => {
  return function(contentBlock, callback, contentState) {
    contentBlock.findEntityRanges(
      (character) => {
        const entityKey = character.getEntity();
        if (entityKey === null) {
          return false;
        }
        return contentState.getEntity(entityKey).getMutability() === mutability;
      },
      callback
    );
  };
}

const getDecoratedStyle = (mutability) => {
  switch (mutability) {
  case 'IMMUTABLE': return styles.immutable;
  default: return null;
  }
}

const TokenSpan = (props) => {
  const style = getDecoratedStyle(
    props.contentState.getEntity(props.entityKey).getMutability()
  );
  return (
    <span data-offset-key={props.offsetkey} style={style}>
      {props.children}
    </span>
  );
};

class EditorComponent extends Component {
  constructor(props) {
    super(props);

    const decorator = new CompositeDecorator([
      {
        strategy: getEntityStrategy('IMMUTABLE'),
        component: TokenSpan,
      }
    ]);

    const blocks = convertFromRaw(this.sentenceToNode());

    this.state = {
      editorState: EditorState.createWithContent(blocks, decorator),
    };

    this.onChange = (editorState) => {
      this.setState({ editorState })
      this.props.onChange(this.nodeToSentence(editorState));
    };

    // focus method causes scrolltop in Chrome after v61
    this.focus = () => this.refs.pendingTextEditArea.focus();
  }

  textToNode(textInput) {
    const outputList = [];
    const textList = textInput.split('\n');

    _.each(textList, text => {
      if (text.match(ilvlRegExp)) {
        _.each(text.match(ilvlRegExp), x => {
          const s = x.split(ilvlRegExpLocal);
          outputList.push({
            text: s[s.length - 1], // Getting the last item in array
            meta: {
              lvlRegex: x.match(ilvlRegExpLocal)[0]
            }
          });
        });
      } else {
        outputList.push({ text });
      }
    });

    return _.chain(outputList)
      .map(this.textToBlock)
      .filter(Boolean)
      .value();
  }

  textToBlock(textMap) {
    const { text, meta } = textMap;
    const t = text.replace(nbrRegExp, '$1 ');
    const entityRanges = text.match(nbrRegExp) && [{
      key: 'number',
      offset: 0,
      length: text.match(nbrRegExp)[1].indexOf('.') !== -1 ? t.indexOf('.') + 2 : 1
      // Need to check if it's a numbered bullet point and not any bullet point. i.e. __/NBR/•/__ vs __/NBR/v./__
    }];

    return {
      text: text.replace(nbrRegExp, '$1 '),
      type: 'unstyled',
      entityRanges,
      data: {
        ... meta,
        numRegex: text.match(nbrRegExp) && text.match(nbrRegExp)[0]
      }
    }
  }

  sentenceToNode() {
    const { text } = this.props;
    return {
      blocks: this.textToNode(text),
      entityMap: {
        number: {
          type: 'TOKEN',
          mutability: 'IMMUTABLE',
        }
      },
    };
  }

  nodeToSentence(editorState) {
    const content = convertToRaw(editorState.getCurrentContent());
    const bulletRegex = /\d\.\s+|[a-z]\)\s+|•\s+|[A-Z]\.\s+|[IVX]+\.\s+/g;
    const NEW_LINE_CHAR = '\n';

    let sentence = _.chain(content.blocks)
      .reduce((output, obj) => {
        const { text, data } = obj;
        // In case of empty text, should return
        if (!text) return output;

        const { numRegex, lvlRegex } = data;
        if (lvlRegex) {
          output += lvlRegex;
        }

        if (numRegex) {
          output += numRegex;
          // Assuming numbering is in form of `ii. `, so splitting on fullstop,
          // if number regex is given
          // Replacing with other bullet regex
          output += text.substr(text.indexOf('. ') + 1, text.length).replace(bulletRegex, '').trim();
        } else {
          output += text;
        }

        // All indent-levels (except the last one) should have a line-break at the end
        if (lvlRegex) {
          output += LBR_MARKER;
        } else { // As the text was split on a new line, add it back, otherwise __/BR/__ accounts for change
          output += NEW_LINE_CHAR;
        }

        return output;
      }, '')
      .value();

    // Remove the last line-break
    if (sentence.endsWith(LBR_MARKER)) {
      sentence = sentence.slice(0, -LBR_MARKER.length);
    } else if (sentence.endsWith(NEW_LINE_CHAR)) { // If last item is a new line character then ignore.
      sentence = sentence.slice(0, -NEW_LINE_CHAR.length);
    }
    return sentence;
  }

  render() {
    return (
      <div style={styles.root}>
        <div style={styles.editor}>
          <Editor
            ref="pendingTextEditArea"
            editorState={this.state.editorState}
            onChange={this.onChange}
          />
        </div>
      </div>
    )
  }
}

// Have to do styles here as they seem to be overriden in the editor
const styles = {
  root: {
    width: '100%',
  },

  editor: {
    cursor: 'text',
    minHeight: 80,
    padding: 10,
    backgroundColor: 'white',
    border: '1px solid #ccc',
  },

  immutable: {
    backgroundColor: 'rgb(234, 234, 234)',
    padding: '2px',
    margin: '2px',
    borderRadius: '4px',
    border: '1px solid rgb(224, 224, 224)',
  }
};

EditorComponent.propTypes = {
  text: React.PropTypes.string.isRequired
}

export default EditorComponent;
