import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle } from 'lucide-react';
import { EvidenceGroups } from './EvidenceGroups';
import { Criterion, Judgement, Importance } from 'types/diagnosis';

interface Props {
  diagnosis: string;
  rank: number;
  tied: boolean;
  criteria: Record<string, Importance>;
  canonical: Criterion[];
  judgements: Record<string, Judgement>;
  grounded: boolean;
}

export const CandidateCard: React.FC<Props> = ({
  diagnosis, rank, tied, criteria, canonical, judgements, grounded,
}) => (
  <Card className="shadow-sm">
    <CardHeader className="pb-3">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <CardDescription className="text-xs mb-1">
            Rank {rank}{tied && ' · tied'}
          </CardDescription>
          <CardTitle className="text-lg font-display">{diagnosis}</CardTitle>
        </div>
        {!grounded && (
          <Badge variant="outline" className="text-[10px] gap-1">
            <AlertCircle className="h-3 w-3" />
            Ungrounded criteria
          </Badge>
        )}
      </div>
    </CardHeader>
    <CardContent>
      <EvidenceGroups criteria={criteria} canonical={canonical} judgements={judgements} />
    </CardContent>
  </Card>
);
