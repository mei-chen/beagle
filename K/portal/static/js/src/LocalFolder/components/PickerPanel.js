import React from "react";
import PropTypes from "prop-types";
import { Panel, Button, Grid, Col, ButtonToolbar } from "react-bootstrap";
import { UFileField } from "base/components/UnboundFields";


const PickerPanel = (props) => (
  <Panel>
    <form>
      <Grid>
        <Col md={3} sm={3} xs={12}>
          <UFileField
            id="batchFile"
            name="file"
            multiple
            onChange={props.onFormFieldChange}
            help={`Max upload size: ${window.CONFIG.MAX_UPLOAD_SIZE / 1024 / 1024} MB`}
          />
        </Col>
        <Col md={9} sm={9} xs={12}>
          <ButtonToolbar className="pull-right">
            <Button bsSize="small" onClick={props.onAddAsBatchClick} disabled={!props.isFileSelected}>
              Upload as a batch
            </Button>
            <Button bsSize="small" onClick={props.onAddToBatchClick} disabled={!props.isFileSelected}>
              Add to a batch
            </Button>
          </ButtonToolbar>
        </Col>
      </Grid>
    </form>
  </Panel>
);

PickerPanel.propTypes = {
  onAddAsBatchClick: PropTypes.func.isRequired,
  onAddToBatchClick: PropTypes.func.isRequired,
  onFormFieldChange: PropTypes.func.isRequired,
  isFileSelected: PropTypes.bool.isRequired
};

export default PickerPanel;
