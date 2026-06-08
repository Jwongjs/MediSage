import styled from 'styled-components';
import { media } from 'utils/media';

const OverTitle = styled.span`
  display: block;
  text-align: left;
  &::before {
    bottom: -0.1em;
    content: '';
    display: inline-block;
    width: 0.9em;
    height: 0.9em;
    background-color: rgb(var(--primary));
    line-height: 0;
  }

  font-size: 1.3rem;
  letter-spacing: 0.02em;
  font-weight: bold;
  line-height: 0;
  text-transform: uppercase;

  ${media('<=desktop')} {
    line-height: 1.5;
  }
`;

export default OverTitle;
