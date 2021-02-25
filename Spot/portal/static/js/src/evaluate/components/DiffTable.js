import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { List } from 'immutable';
import { Pagination } from 'react-bootstrap';
import DiffItem from './DiffItem';

import { getDiffFromServer, simulateDiffOnServer } from 'evaluate/redux/modules/diff_module';

class DiffTable extends Component {
  constructor(props) {
    super(props);
    this._getSamples = this._getSamples.bind(this);
    this._renderSamples = this._renderSamples.bind(this);
    this._handlePaginationClick = this._handlePaginationClick.bind(this);
    this.state = {
      isOpen: true,
      page: 1
    }
  }

  componentWillMount() {
    this._getSamples()
  }

  _getSamples() {
    const { getDiffFromServer, id } = this.props;
    const { page } = this.state;
    getDiffFromServer(id, page)
  }

  _handlePaginationClick(page) {
    this.setState({ page }, this._getSamples);
  }

  _renderSamples(samples) {
    const { simulateDiffOnServer, id } = this.props;
    const { page } = this.state;

    return samples.map((sample, i) => {
      const gold = sample.get('gold');
      const label = sample.get('label');
      const text = sample.get('text');
      const simulationTaskUuid = `DIFF_SIMULATION:${(page-1)*10+i}`; // task uuid starts with DIFF_SIMULATION to distinguish from main simulation task on front-end

      return (
        <DiffItem
          key={simulationTaskUuid}
          gold={gold}
          text={text}
          label={label}
          simulationTaskUuid={simulationTaskUuid}
          onSimulate={() => simulateDiffOnServer(simulationTaskUuid, id, text) }/>
      )
    });
  }

  render() {
    const { samples, count } = this.props;
    const { page } = this.state;

    return (
      <div className="diff">
        <div className="diff-table">
          <div className="diff-table-head clearfix">
            <div className="diff-table-th">Gold</div>
            <div className="diff-table-th">Predicted</div>
          </div>
          <div className="diff-table-body">
            { this._renderSamples(samples) }
          </div>
        </div>

        <div className="diff-pagination">
          <Pagination
            activePage={page}
            items={ Math.ceil(count/10) }
            prev
            next
            boundaryLinks
            ellipsis
            maxButtons={5}
            onSelect={this._handlePaginationClick}
          />
        </div>
      </div>
    )
  }
}

DiffTable.propTypes = {
  id: PropTypes.number.isRequired,
  samples: PropTypes.instanceOf(List).isRequired,
  count: PropTypes.number.isRequired
}

const mapStateToProps = state => {
  return {
    samples: state.diffModule.get('samples'),
    count: state.diffModule.get('count')
  }
};

const mapDispatchToProps = dispatch => {
  return bindActionCreators({
    getDiffFromServer,
    simulateDiffOnServer
  }, dispatch)
}

export default connect(mapStateToProps, mapDispatchToProps)(DiffTable);
