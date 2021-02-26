import React from 'react';

const DummyTile = () => {
  return (
    <div className="tile project-tile closed dummy">
      <div className="tile-header">
        <span className="owner-avatar" />
        <div className="project-title">
          <div className="project-type" />
          <div className="project-name-wrapper" />
        </div>
      </div>

      <div className="tile-body">
        <div className="party-wrapper">
          <div className="party">
            <span className="dummy-icon" />
            <span className="dummy-party" />
          </div>
          <div className="party">
            <span className="dummy-icon" />
            <span className="dummy-party" />
          </div>
        </div>
        <div className="tile-trigger">
          <div className="arrow-container" />
        </div>
      </div>
    </div>
  )
}

const DummyTiles = () => {
  return (
    <div className="project-tiles">
      <div className="project-column">
        <DummyTile />
        <DummyTile />
        <DummyTile />
      </div>
      <div className="project-column">
        <DummyTile />
        <DummyTile />
        <DummyTile />
      </div>
    </div>
  )
}

export default DummyTiles;
