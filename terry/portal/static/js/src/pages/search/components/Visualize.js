import React, { Component } from 'react';
import BarChart from './BarChart';

class Visualize extends Component {
  constructor(props) {
    super(props);
    this._barData = this._barData.bind(this);
    this._overallBarData = this._overallBarData.bind(this);
    this._renderCharts = this._renderCharts.bind(this);
  }

  _barData(data, stats) {
    return Object.keys(data).map(key => {
      const targetStat = stats.filter(stat => stat[0] === key)[0];

      return {
        label: key,
        value: data[key],
        barsData: [
          targetStat[3] === null ? null : targetStat[3] / 100,
          targetStat[4] === null ? null : targetStat[4] / 100
        ]
      }
    });
  }

  _overallBarData(stats) {
    return stats.map(stat => ({
      label: stat[0],
      value: stat[1],
      barsData: [
        stat[3] === null ? null : stat[3] / 100,
        stat[4] === null ? null : stat[4] / 100
      ]
    }))
  }

  _renderCharts() {
    const { stats, statsByPm } = this.props;
    const pmNames = Object.keys(statsByPm);

    // if multiple package managers: display Overall chart and one chart for each pm 
    if(pmNames.length > 1) {
      return (
        <div>
          <BarChart
            title="Overall"
            data={this._overallBarData(stats)}
            open={true}
          />
          { pmNames.map((pm, i) => (
            <BarChart
              key={i}
              title="Overall"
              title={pm}
              data={this._barData(statsByPm[pm], stats)}
            />
          )) }
        </div>
      )
    // if one package manager: display Overall chart with subtitle
    } else {
      return (
        <BarChart
          title="Overall"
          subtitle={pmNames[0]}
          data={this._overallBarData(stats)}
          open={true}
        />
      )
    }
  }

  render() {
    
    return(
      <div className="visualize">
        { this._renderCharts() }
      </div>
    )
  }
}

export default Visualize;
