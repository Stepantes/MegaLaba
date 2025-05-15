import React from "react";
import styles from "./DashboardHistoryPanel.module.css";

const ArrowUp = () => (
  <span className={styles.arrowUp} title="Выше целевого">&#8593;</span>
);

const ArrowDown = () => (
  <span className={styles.arrowDown} title="Ниже целевого">&#8595;</span>
);

const CheckMark = () => (
  <span className={styles.checkMark} title="В пределах нормы">&#10003;</span>
);

const Indicator = ({ actual, target }) => {
  if (Math.abs(actual - target) <= 1.5) return <CheckMark />;
  if (actual > target) return <ArrowUp />;
  return <ArrowDown />;
};

const TargetVsActualBlock = ({ targets, actuals }) => {
  const indicators = [
    {
      key: "temperature",
      label: "Температура",
      unit: "°C",
    },
    {
      key: "humidity",
      label: "Влажность",
      unit: "%",
    },
    {
      key: "light",
      label: "Освещённость",
      unit: "лк",
    },
  ];

  return (
    <div className={styles.targetActualPanel}>
      <div className={styles.targetActualTitle}>Целевые и фактические показатели</div>
      <div className={styles.targetActualTable}>
        <div className={styles.targetActualHeader}>
          <span>Показатель</span>
          <span>Целевое</span>
          <span>Фактическое</span>
          <span>Статус</span>
        </div>
        {indicators.map(({ key, label, unit }) => (
          <div className={styles.targetActualRow} key={key}>
            <span>{label}</span>
            <span>
              {targets[key] !== undefined && targets[key] !== null ? targets[key] : "--"} {unit}
            </span>
            <span>
              {actuals[key] !== undefined && actuals[key] !== null ? actuals[key] : "--"} {unit}
            </span>
            <span>
              {targets[key] !== undefined &&
              targets[key] !== null &&
              actuals[key] !== undefined &&
              actuals[key] !== null ? (
                <Indicator actual={actuals[key]} target={targets[key]} />
              ) : (
                ""
              )}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TargetVsActualBlock;