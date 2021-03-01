import React from 'react';
import { Grid, Col } from 'react-bootstrap';
import FormatConvertingPanel from 'FormatConverting/components/FormatConvertingPanel';


class ContentComponent extends React.Component {
  render() {
    return (
      <div>
        <Grid>
          <Col xs={12} md={12}>
            <FormatConvertingPanel />
          </Col>
        </Grid>
      </div>
    );
  }
}

export default ContentComponent;
