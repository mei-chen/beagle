import React from 'react';
import { Button, ButtonToolbar } from 'react-bootstrap';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import ModalForm from 'base/components/ModalForm';
import { postRegExs, patchRegEx, deleteRegEx, getRegExs } from 'base/redux/modules/regexes';
import { setModalOpen, deselectRegEx } from 'RegEx/redux/actions';
import RegExForm from 'RegEx/components/forms';
import RegExPanel from 'RegEx/components/RegExPanel';
import RegexSearchController from 'RegEx/components/RegexSearchController';
import PreviewRegexPopup from 'RegEx/components/PreviewRegexPopup';

import { MODULE_NAME } from 'RegEx/constants';

import '../scss/ContentComponent.scss'

class ContentComponent extends React.Component {
  constructor(props) {
    super(props);
    this.editRegExSubmit = this.editRegExSubmit.bind(this);
    this.deleteRegExSubmit = this.deleteRegExSubmit.bind(this);
  }

  editRegExSubmit(data) {
    const { patchRegEx, selectedRegEx, setModalOpen, deselectRegEx } = this.props;
    return patchRegEx(
      selectedRegEx.get('resource_uri'), data,
      [() => setModalOpen('edit', false), () => deselectRegEx()]
    );
  }

  deleteRegExSubmit() {
    const { deleteRegEx, selectedRegEx, setModalOpen, deselectRegEx } = this.props;
    deleteRegEx(
      selectedRegEx.get('resource_uri'),
      [() => setModalOpen('delete', false), () => deselectRegEx()]
    );
  }

  componentWillMount() {
    this.props.getRegExs();
  }

  render() {
    const { isModalOpen, setModalOpen, postRegExs, selectedRegEx, selectedReport } = this.props;
    return (
      <div className="wrapper">
        <RegexSearchController />
        <PreviewRegexPopup
          isOpen={isModalOpen.get('preview')}
          report={selectedReport}
          onClose={() => setModalOpen('preview', false)}
          title="Report Preview"
        />
        <ModalForm
          isOpen={isModalOpen.get('create')}
          onClose={() => setModalOpen('create', false)}
          title="Create new RegEx"
        >
          <RegExForm
            submit_label='Create'
            name=''
            content=''
            onSubmit={data => postRegExs(data, () => setModalOpen('create', false))}
            onClose={() => setModalOpen('create', false)}
          />
        </ModalForm>

        <ModalForm
          isOpen={isModalOpen.get('edit')}
          onClose={() => setModalOpen('edit', false)}
          title={`Edit RegEx ${selectedRegEx.get('name')}`}
        >
          <RegExForm
            name={selectedRegEx.get('name')}
            content={selectedRegEx.get('content')}
            submit_label='Edit'
            onSubmit={this.editRegExSubmit}
            onClose={() => setModalOpen('edit', false)}
          />
        </ModalForm>

        <ModalForm
          isOpen={isModalOpen.get('delete')}
          onClose={() => setModalOpen('delete', false)}
          title="Are You Sure?"
        >
          <div className="text-center">
            <p>
              <strong>Do you want delete `{selectedRegEx.get('name')}`?</strong>
            </p>
            <ButtonToolbar style={{display: 'inline-block'}}>
              <Button
                bsStyle="danger"
                onClick={this.deleteRegExSubmit}
              >
                Yes
              </Button>
              <Button onClick={() => setModalOpen('delete', false)}>No</Button>
            </ButtonToolbar>
          </div>
        </ModalForm>

      </div>
    );
  }
}

const mapDispatchToProps = dispatch => bindActionCreators({
  postRegExs,
  patchRegEx,
  deleteRegEx,
  setModalOpen,
  deselectRegEx,
  getRegExs
}, dispatch);

const mapStateToProps = state => ({
  selectedRegEx: state[ MODULE_NAME ].get('selectedRegEx'),
  selectedReport: state[ MODULE_NAME ].get('selectedReport'),
  regexes: state[ MODULE_NAME ].get('regexes'),
  isModalOpen: state[ MODULE_NAME ].get('isModalOpen')
});

export default connect(mapStateToProps, mapDispatchToProps)(ContentComponent);
