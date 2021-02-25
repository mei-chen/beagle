import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Link } from 'react-router';
import { FormControl, FormGroup, Checkbox, Button, Alert } from 'react-bootstrap';

import {
  resetCollect,
  collectOnServer
} from 'create-experiment/redux/modules/online_db_module';


class CollectForm extends Component {
  constructor(props) {
    super(props);
    this._handleSaveClick = this._handleSaveClick.bind(this);

    this.state = {
      name: '',
      includeInferred: true
    }
  }

  componentDidMount() {
    this.props.resetCollect();
  }

  _handleSaveClick() {
    const { uuid, tag, collectOnServer } = this.props;
    const { name, includeInferred } = this.state;

    if(name) {
      collectOnServer(uuid, tag, name, includeInferred);
    }
  }

  render() {
    const { name, includeInferred } = this.state;
    const { collecting } = this.props;

    return (
      <div className="collect">
        { collecting.get('isSuccess') ? (
          <Alert bsStyle="success">
            Data moved to
            <Link
              className="saved-dataset-link"
              to={`/datasets/${collecting.get('data').get('id')}/page/1`}>
              <i className="fa fa-database" />
              <span>{ collecting.get('data').get('name') }</span>
            </Link>
            <br />
            Don't forget to add it to your Classifiers.
          </Alert>
        ) : (
          <div className="collect-form">
            <FormGroup>
              <FormControl
                type="text"
                value={name}
                placeholder="Dataset name"
                onChange={e => this.setState({ name: e.target.value })} />
            </FormGroup>

            <FormGroup>
              <Checkbox
                checked={includeInferred}
                onChange={e => this.setState({ includeInferred: e.target.checked })}>
                Include inferred
              </Checkbox>
            </FormGroup>

            <Button
              bsStyle="primary"
              onClick={this._handleSaveClick}
              disabled={collecting.get('isLoading') || !name}>
              Save { collecting.get('isLoading') && <i className="fa fa-spinner fa-spin" /> }
            </Button>
          </div>
        ) }
      </div>
    )
  }
};

CollectForm.propTypes = {
  uuid: PropTypes.string.isRequired,
  tag: PropTypes.string.isRequired
};

const mapStateToProps = state => ({
  uuid: state.createExperimentModule.get('uuid'),
  collecting: state.onlineDbModule.get('collecting')
});

const mapDispatchToProps = dispatch => bindActionCreators({
  resetCollect,
  collectOnServer
}, dispatch)

export default connect(mapStateToProps, mapDispatchToProps)(CollectForm);
