import React from "react";
import { ArrowUpRight, CheckCircle2, FileText, Wrench } from "lucide-react";

const icons = {
  payment: <CheckCircle2 size={17} />,
  maintenance: <Wrench size={17} />,
  invoice: <ArrowUpRight size={17} />,
  lease: <FileText size={17} />,
};

export default function ActivityList({ activities }) {
  return (
    <div className="activity-list">
      {activities.map((activity) => (
        <div className="activity-row" key={activity.id}>
          <div className={`activity-icon ${activity.type}`}>
            {icons[activity.type] || <FileText size={17} />}
          </div>
          <div className="activity-content">
            <strong>{activity.title}</strong>
            <span>{activity.description}</span>
          </div>
          <time>{activity.date}</time>
        </div>
      ))}
    </div>
  );
}