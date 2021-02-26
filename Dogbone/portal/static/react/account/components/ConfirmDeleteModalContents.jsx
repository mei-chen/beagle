/*
 * This component renders a warning to confirm a deletion of
 * a document is what the user actually wants to do.
 */

import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import Button from 'react-bootstrap/lib/Button';
import ButtonToolbar from 'react-bootstrap/lib/ButtonToolbar';

// App
import { deleteDocument, rejectDocument } from '../redux/modules/project';

const ConfirmDeleteModalContents = React.createClass({

  deleteDocument() {
    const {
      project,
      isDelete,
      isReject
    } = this.props;
    if (isDelete) {
      this.props.deleteDocument(project);
    } else if (isReject) {
      this.props.rejectDocument(project);
    }
    this.props.closeProp();

    //set the deleted tile state to closed
    this.props.closeTile();
  },

  cancelDeleteDocument() {
    this.props.closeProp();
  },

  render() {
    const { batch, docs } = this.props.project;
    const styles = {
      header: {
        background: '#5D101A',
        padding: '20px 0 10px 20px'
      },
      contents: {
        padding: 15
      },
      modaltextline: {
        color: 'black'
      },
      well: {
        padding: '5px',
        borderRadius: '10px',
        border: '1px solid #cacaca',
        margin: '5px 0 10px 0',
        display: 'block',
        overflowWrap: 'break-word'
      },
      heading: {
        fontFamily: "'proxima-nova', Helvetica, Arial, sans-serif",
        fontSize: '1.2em',
        display: 'block',
        paddingTop: 3,
        paddingBottom: 3
      },
      full: {
        width: '100%',
        clear: 'both',
        paddingTop: 10
      },
      title: {
        fontFamily: "'proxima-nova', Helvetica, Arial, sans-serif",
        fontSize: '1.5em',
        paddingBottom: 5,
        color: '#fff'
      },
    };

    var documents;

    if (batch) {
      documents = docs.map((v,k) => {
        return (
          <span style={styles.well} key={k}>
            <i className="fa fa-file-alt" /> {v.title}
          </span>
        )
      })
    } else {
      documents = (<span style={styles.well}>
        <i className="fa fa-file-alt" /> {this.props.project.title}
      </span>);
    }

    /*
     * force the modal to be a maxiumum of 300px
     * by injecting this extra CSS
     */
    return (
      <div className="delete-modal">
        <div style={styles.header}>
          <span style={styles.title} >
            {
              this.props.isDelete ?
              `Delete Document${batch && docs.length > 1 ? 's' : ''}?` :
              `Reject Invite${batch && docs.length > 1 ? 's' : ''}?`
            }
          </span>
        </div>
        <div style={styles.contents}>
          <div style={styles.heading}>
            <p style={styles.modaltextline}>
              {
                this.props.isDelete ?
                `Deleting ${batch && docs.length > 1 ? 'these documents' : 'this document'} is permanent. Are you sure?` :
                `You will lose access to ${batch && docs.length > 1 ? 'these documents' : 'this document'}. Are you sure?`
              }
            </p>
            <p style={styles.modaltextline}>
              {documents}
            </p>
          </div>
          <ButtonToolbar>
              <Button onClick={this.deleteDocument} bsStyle="danger">
                {
                  this.props.isDelete ?
                  'Confirm Delete' :
                  'Confirm Reject'
                }
              </Button>
              <Button onClick={this.cancelDeleteDocument} >Cancel</Button>
          </ButtonToolbar>
        </div>
      </div>
    );
  }

});

const mapDispatchToProps = (dispatch) => {
  return bindActionCreators({ deleteDocument, rejectDocument }, dispatch);
}

export default connect(null, mapDispatchToProps)(ConfirmDeleteModalContents);
