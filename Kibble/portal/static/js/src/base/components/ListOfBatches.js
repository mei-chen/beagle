import React from "react";
import { connect } from "react-redux";
import { bindActionCreators } from "redux";
import { Table } from "react-bootstrap";
import { getBatches } from "base/redux/modules/batches";
import "base/scss/ListOfBatches.scss";


const BatchTableRow = ({ batch }) => (
  <tr>
    <td>{batch.name}</td>
    <td>{batch.status || 'N/A'}</td>
    <td>{batch.filecount}</td>
    <td>{batch.upload_error || '-'}</td>
    <td>{batch.upload_date}</td>
    <td>{batch.upload_time}</td>
    <td>{batch.process_time || 'N/A'}</td>
    <td>{batch.owner_username || '-'}</td>
  </tr>
);

class ListOfBatches extends React.Component {

  componentDidMount() {
    this.props.getBatches();
  }

  render() {
    return (
      <Table striped bordered condensed hover responsive>
        <thead>
        <tr>
          <th>Batch Name</th>
          <th>Status</th>
          <th>Files</th>
          <th>Upload error</th>
          <th>Upload date</th>
          <th>Upload time</th>
          <th>Process time</th>
          <th>Owner</th>
        </tr>
        </thead>
        <tbody>
        {
          this.props.batchStore.map(
            batch => <BatchTableRow key={batch.id} batch={batch}/>)
        }
        </tbody>
      </Table>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    batchStore: state.global.batches
  };
};

const mapDispatchToProps = (dispatch) => {
  return bindActionCreators({ getBatches }, dispatch)
};

export default connect(mapStateToProps, mapDispatchToProps)(ListOfBatches);
