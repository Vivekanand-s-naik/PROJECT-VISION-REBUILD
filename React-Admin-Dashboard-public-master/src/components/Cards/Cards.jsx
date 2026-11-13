import React from "react";
import "./Cards.css";
import Card from "../Card/Card";

const Cards = ({ cards }) => {
  if (!cards || cards.length === 0) {
    return (
      <div style={{ color: "#94a3b8", padding: "20px", textAlign: "center" }}>
        Loading user telemetry cards...
      </div>
    );
  }

  return (
    <div className="Cards">
      {cards.map((card, id) => (
        <div className="parentContainer" key={id}>
          <Card
            title={card.title}
            color={card.color}
            barValue={card.barValue}
            value={card.value}
            metric_label={card.metric_label}
            png={card.png}
            series={card.series}
          />
        </div>
      ))}
    </div>
  );
};

export default Cards;
