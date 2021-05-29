import React from 'react';

import {
  ToggleButtonGroup,
  ToggleButton,
  ButtonToolbar,
  Button,
  Modal,
  Label,
  OverlayTrigger,
  Popover
} from 'react-bootstrap';
import Select from 'react-select';

import { MODULE_NAME, ACTIVE, OBFUSCATION_TYPE} from 'Settings/redux/constants';

export class PersonalDataTypeCustomizationModal extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      selected_type:"",
      input_text: "",
      new_entry_type:"word",
      expanded_footer: false,
      select_all: [undefined,undefined],
    }

    this.handleTypeAction = this.handleTypeAction.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleEntryTypeChange = this.handleEntryTypeChange.bind(this);
    this.handleSelectTypeChange = this.handleSelectTypeChange.bind(this);
    this.handleAddNewEntry = this.handleAddNewEntry.bind(this);
    this.handleSetAll = this.handleSetAll.bind(this);
    this.collapse = this.collapse.bind(this);
  }

  handleTypeAction(type,setting_to_change,value) {
    var { changeSetting, personal_data_types } = this.props;

    personal_data_types[type][setting_to_change] = value;
    changeSetting('personal_data_types',personal_data_types);

    var current_state = this.state.select_all;
    current_state[setting_to_change] = undefined;
    this.setState({select_all: current_state});

  }

  handleSetAll(field,value) {
    var { changeSetting, personal_data_types } = this.props;

    var current_state = this.state.select_all;
    current_state[field] = value;
    this.setState({select_all: current_state})

    Object.keys(personal_data_types).map(type => {
      personal_data_types[type][field] = value;
    })

    changeSetting('personal_data_types',personal_data_types);
  }

  handleInputChange(e) {
    this.setState({
      input_text: e.target.value
    })
  }

  handleEntryTypeChange(value) {
    this.setState({
      new_entry_type: value
    })
  }

  handleAddNewEntry() {
    const is_regex = this.state.new_entry_type === 'regex';
    this.props.addPersonalDataType(this.state.selected_type.value, this.state.input_text, is_regex )
    .then(
      this.setState({
        input_text:""
      })
    )
  }

  handleSelectTypeChange(value) {
    this.setState({
      selected_type: value
    })
  }

  collapse(new_state = undefined) {

    this.setState({
      expanded_footer: new_state ? new_state : !this.state.expanded_footer
    });
  }

  render() {
    const {
      changeSetting,
      deletePersonalDataType,
      personal_data_types,
      custom_personal_data,
      custom_type_names,
      change_success,
      onClose,
      isOpen
    } = this.props;

    const popover = (
      <Popover id="popover-positioned-right" title={(<strong>Hint!</strong>)}>
        The personal information types list will automatically update with new types when they are found in your uploaded documents.
      </Popover>
    );
    return(
       <Modal show={isOpen} bsSize="large" onHide={() => onClose(!isOpen)}>

        <Modal.Header closeButton={true} className={this.state.expanded_footer ? "shadowed-modal" : ""}>
          <Modal.Title>
            Customize personal data types{" "}
            <OverlayTrigger trigger="click" placement="right" overlay={popover}>
              <i className="fal fa-info-circle hint"></i>
            </OverlayTrigger>
            <div className="check-mark-wrapper no-margin">
              { change_success === 'success' &&
                <div className="check-mark">
                  <i className="fal fa-check"/> Successfully changed settings
                </div>
              }
              { change_success === 'fail' &&
                <div className="check-mark">
                  <i className="fal fa-times"/> Failed changing settings
                </div>
              }
            </div>
          </Modal.Title>
          <div className="table-header">
            <div>Active</div>
            <div className="name-label">
              <div>Name</div>
            </div>
            <div className="selected-obf-type-label">
              Obfuscation method
            </div>
          </div>
          <div className="data-type header">
            <div
              className="checkbox"
              onClick={() => this.handleSetAll(ACTIVE,!this.state.select_all[ACTIVE])}
            >
             {this.state.select_all[ACTIVE] ?
                <i className="fal fa-check-square"></i> :
                <i className="fal fa-square"></i>
              }
            </div>
            <div className="name">
              Set all
            </div>
            <div className="selected-obf-type">
              <ButtonToolbar>
                <ToggleButtonGroup
                  type="radio"
                  name="obf-method"
                  value={this.state.select_all[OBFUSCATION_TYPE]}
                  onChange={value => this.handleSetAll(OBFUSCATION_TYPE,value)}
                >
                  <ToggleButton className="black_out" value={'black_out'}><i className="fal fa-eye-slash"/>{" "}Black out</ToggleButton>
                  <ToggleButton className="string" value={'string'}><i className="fal fa-sync-alt"/>{" "}Replace</ToggleButton>
                  <ToggleButton className="highlight" value={'highlight'}><i className="fal fa-pen-alt"/>{" "}Highlight</ToggleButton>
                  <ToggleButton className="none" value={'none'}><i className="fal fa-eye"></i>{" "}None</ToggleButton>
                </ToggleButtonGroup>
              </ButtonToolbar>
            </div>
          </div>
        </Modal.Header>

        <Modal.Body className={`scrollable-modal-body ${this.state.expanded_footer ? "expanded-footer" : ""}`}>
        {
          Object.keys(personal_data_types).map((type, i) => {
            return (
              <div key={i} className="data-type">
                <div
                  className="checkbox"
                  onClick={() => this.handleTypeAction(type,ACTIVE,!personal_data_types[type][ACTIVE])}
                >
                  {personal_data_types[type][ACTIVE] ?
                    <i className="fal fa-check-square"></i> :
                    <i className="fal fa-square"></i>
                  }
                </div>
                <div className="name">
                  {type}
                  {custom_type_names.includes(type) &&
                    <div
                      className="customize-action"
                      onClick={() => {
                        this.handleSelectTypeChange({value: type, label: type})
                        this.collapse(true);
                      }}
                    >
                      <div className="custom-tooltip">Customize</div>
                      <i className="far fa-star"></i>
                    </div>
                  }
                </div>
                <div className="selected-obf-type">
                  <ButtonToolbar>
                    <ToggleButtonGroup
                      type="radio"
                      name="obf-method"
                      value={personal_data_types[type][OBFUSCATION_TYPE]}
                      onChange={value => this.handleTypeAction(type,OBFUSCATION_TYPE,value)}
                    >
                      <ToggleButton className="black_out" value={'black_out'}><i className="fal fa-eye-slash"/>{" "}Black out</ToggleButton>
                      <ToggleButton className="string" value={'string'}><i className="fal fa-sync-alt"/>{" "}Replace</ToggleButton>
                      <ToggleButton className="highlight" value={'highlight'}><i className="fal fa-pen-alt"/>{" "}Highlight</ToggleButton>
                      <ToggleButton className="none" value={'none'}><i className="fal fa-eye"></i>{" "}None</ToggleButton>
                    </ToggleButtonGroup>
                  </ButtonToolbar>
                </div>
              </div>
            )
          })
        }
        </Modal.Body>

        <Modal.Footer className={this.state.expanded_footer ? "shadowed-modal" : ""}>
          <div className={`add-type ${this.state.expanded_footer ? "expanded-footer" : ""}`}>
            <div>
              <Button bsStyle="success" onClick={() => this.collapse()}>
                {this.state.expanded_footer ?
                  <i className="fal fa-chevron-down"></i> :
                  <i className="fal fa-chevron-up"></i>
                }{" "}
                Manage your custom types
              </Button>
              <Button bsStyle="danger"  onClick={() => onClose(!isOpen)}>Close</Button>
            </div>
            <div className="mange-form">

              <h4>Select one of your personal types or type a new one</h4>
              <Select.Creatable
                multi={false}
                options={custom_type_names.map(type => ({value: type, label: type}))}
                onChange={this.handleSelectTypeChange}
                value={this.state.selected_type}
              />

              <h4> Your selected personal type entries </h4>
              <div className="type-entries">
              {this.state.selected_type === "" ?
                <h5> First select a type </h5> :
                custom_personal_data.map((entry,key) => {
                  return entry.type === this.state.selected_type.value ?
                    <Label key={key} bsStyle="primary">
                      {entry.text}
                      <i
                        title="Delete entry"
                        onClick={() => deletePersonalDataType(entry.uuid)} className="fal fa-trash-alt"
                      />
                    </Label> :
                    ''
                })
              }
              </div>

              <h4> Add a new entry in your selected type </h4>
              {this.state.selected_type === "" ?
                <h5> First select a type </h5> :
                <div className="new-entry">
                  <input
                    className="add-input"
                    placeholder="Type a word or a regex..."
                    onChange={this.handleInputChange}
                    onKeyDown={e => e.keyCode === 13 && this.handleAddNewEntry()}
                    value={this.state.input_text}
                  />
                  <Button onClick={this.handleAddNewEntry}>Save as</Button>
                  <ButtonToolbar>
                    <ToggleButtonGroup
                      type="radio"
                      name="entry-type"
                      onChange={this.handleEntryTypeChange}
                      value={this.state.new_entry_type}
                    >
                      <ToggleButton value={'word'}>KeyWord</ToggleButton>
                      <ToggleButton value={'regex'}>RegEx</ToggleButton>
                    </ToggleButtonGroup>
                  </ButtonToolbar>
                </div>
              }

            </div>
          </div>
        </Modal.Footer>

      </Modal>
    )
  }
}
