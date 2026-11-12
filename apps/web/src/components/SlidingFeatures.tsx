import React from 'react';
import { Card } from './Card';
import { LucideIcon } from 'lucide-react';

export interface Feature {
  icon: LucideIcon;
  title: string;
  description: string;
  details: string[];
}

interface SlidingFeaturesProps {
  features: Feature[];
}

export const SlidingFeatures: React.FC<SlidingFeaturesProps> = ({ features }) => {
  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      {features.map((feature, idx) => {
        const IconComponent = feature.icon;
        return (
          <Card
            key={idx}
            interactive
            className="flex flex-col justify-between h-full bg-white border border-slate-200 hover:border-orange-400 hover:shadow-md transition-all duration-200"
          >
            <div>
              <div className="w-10 h-10 rounded-lg bg-orange-50 border border-orange-100 flex items-center justify-center text-orange-600 mb-4">
                <IconComponent className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2 tracking-tight">{feature.title}</h3>
              <p className="text-slate-600 text-sm leading-relaxed mb-6">{feature.description}</p>
            </div>

            <ul className="space-y-2 pt-4 border-t border-slate-100 text-xs font-mono text-slate-600">
              {feature.details.map((detail, didx) => (
                <li key={didx} className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-orange-500 flex-shrink-0" />
                  <span className="truncate">{detail}</span>
                </li>
              ))}
            </ul>
          </Card>
        );
      })}
    </div>
  );
};
