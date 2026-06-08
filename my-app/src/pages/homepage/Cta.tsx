import React from 'react';
import styled from 'styled-components';
import Button from 'components/homepage/Button';
import ButtonGroup from 'components/homepage/ButtonGroup';
import Container from 'components/homepage/Container';
import OverTitle from 'components/homepage/OverTitle';
import SectionTitle from 'components/homepage/SectionTitle';
import { media } from 'utils/media';

export default function Cta() {
  return (
    <CtaWrapper>
      <Container>
        <Stack>
          <OverTitle>Lorem ipsum dolor sit amet</OverTitle>
          <SectionTitle>
            Lorem ipsum dolor, sit amet consectetur adipisicing elit. Temporibus delectus?
          </SectionTitle>
          <Description>
            Lorem ipsum dolor sit amet consectetur adipisicing elit. Assumenda beatae accusamus deleniti nihil quas tempora numquam, vitae
            culpa.
          </Description>
          <ButtonGroup>
            <a href="#early-access">
              <Button>
                Subscribe to the newsletter <span>&rarr;</span>
              </Button>
            </a>
            <a href="#whitepaper">
              <OutlinedButton transparent>
                Features <span>&rarr;</span>
              </OutlinedButton>
            </a>
          </ButtonGroup>
        </Stack>
      </Container>
    </CtaWrapper>
  );
}

// Styled Components (unchanged)
const Description = styled.div`
  font-size: 1.8rem;
  color: rgba(var(--textSecondary), 0.8);
`;

const Stack = styled.div`
  display: flex;
  flex-direction: column;
  padding: 12.5rem 0;
  color: rgb(var(--textSecondary));
  text-align: center;
  align-items: center;
  justify-content: center;

  & > *:not(:first-child) {
    max-width: 80%;
    margin-top: 4rem;
  }

  ${media('<=tablet')} {
    text-align: center;

    & > *:not(:first-child) {
      max-width: 100%;
      margin-top: 2rem;
    }
  }
`;

const OutlinedButton = styled(Button)`
  border: 1px solid rgb(var(--textSecondary));
  color: rgb(var(--textSecondary));
`;

const CtaWrapper = styled.div`
  background: rgb(var(--secondary));
`;
