import React, { PropsWithChildren } from 'react';
import styled from 'styled-components';

export default function RichText({ children }: PropsWithChildren) {
  return <RichTextWrapper>{children}</RichTextWrapper>;
}

const RichTextWrapper = styled.div`
  font-size: 1.8rem;
  line-height: 1.6;
  color: #333;

  p {
    margin-bottom: 1.5rem;
  }

  ul {
    padding-left: 1.5rem;
    margin-bottom: 1.5rem;
  }

  li {
    margin-bottom: 0.5rem;
  }

  strong {
    font-weight: 600;
  }

  em {
    font-style: italic;
  }
`;
