import { Link as RouterLink } from 'react-router-dom';
import styled from 'styled-components';
import { PropsWithChildren } from 'react';

export interface LinkProps {
  href: string;
}

export default function Link({ href, children }: PropsWithChildren<LinkProps>) {
  return <StyledLink to={href}>{children}</StyledLink>;
}

const StyledLink = styled(RouterLink)`
  display: inline;
  width: fit-content;
  text-decoration: none;

  background: linear-gradient(rgb(var(--primary)), rgb(var(--primary)));
  background-position: 0% 100%;
  background-repeat: no-repeat;
  background-size: 100% 0px;
  transition: 100ms;
  transition-property: background-size, text-decoration, color;
  color: rgb(var(--primary));

  &:hover {
    background-size: 100% 100%;
    text-decoration: none;
    color: rgb(var(--background));
  }

  &:active {
    color: rgb(var(--background));
    background-size: 100% 100%;
  }
`;
