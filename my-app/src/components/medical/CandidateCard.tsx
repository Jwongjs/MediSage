import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ExternalLink } from 'lucide-react';
import { EvidenceGroups } from './EvidenceGroups';
import { Criterion, Judgement, Importance, Explanation } from 'types/diagnosis';

interface Props {
  diagnosis: string;
  rank: number;
  tied: boolean;
  criteria: Record<string, Importance>;
  canonical: Criterion[];
  judgements: Record<string, Judgement>;
  checked: Set<string>;
  onToggle: (key: string) => void;
  explanation: Explanation | null;
}

export const CandidateCard: React.FC<Props> = ({
  diagnosis, rank, tied, criteria, canonical, judgements, checked, onToggle, explanation,
}) => (
  <Card className="shadow-sm">
    <CardHeader className="pb-3">
      <CardDescription className="text-xs mb-1">
        Rank {rank}{tied && ' · tied'}
      </CardDescription>
      <CardTitle className="text-lg font-display">{diagnosis}</CardTitle>
    </CardHeader>
    <CardContent>
      {explanation && (
        <p className="text-sm text-muted-foreground leading-relaxed mb-4">
          {explanation.text}
          {explanation.source && explanation.url && (
            <>
              {' '}
              <a
                href={explanation.url}
                target="_blank"
                rel="noreferrer"
                className="text-primary underline underline-offset-2 inline-flex items-center gap-1 whitespace-nowrap"
              >
                {explanation.source}<ExternalLink className="h-3 w-3" />
              </a>
            </>
          )}
        </p>
      )}
      <EvidenceGroups criteria={criteria} canonical={canonical} judgements={judgements} checked={checked} onToggle={onToggle} />
    </CardContent>
  </Card>
);
