import React from 'react';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
import Button from 'components/homepage/Button';
import ButtonGroup from 'components/homepage/ButtonGroup';
import Container from 'components/homepage/Container';
import HeroIllustration from 'components/homepage/HeroIllustration';
import OverTitle from 'components/homepage/OverTitle';
import { media } from 'utils/media';



export default function Hero() {
  const navigate = useNavigate();

  return (
    <HeroWrapper>
      <Contents>
        <CustomOverTitle>Has your symptoms been bothering you? Look into our</CustomOverTitle>
        <Heading>Step-by-Step AI powered Diagnosis</Heading>
        <Description>
          Quickly understand what might be causing your symptoms with our intelligent, guided diagnosis tool.
          Get insights in minutes — fast, reliable, and private.
        </Description>
      </Contents>
      <ImageContainer>
        <HeroIllustration />
      </ImageContainer>
    </HeroWrapper>
  );
}

const HeroWrapper = styled(Container)`
  display: flex;
  padding-top: 5rem;

  ${media('<=desktop')} {
    padding-top: 1rem;
    flex-direction: column;
    align-items: center;
  }
`;

const Contents = styled.div`
  flex: 1;
  max-width: 60rem;

  ${media('<=desktop')} {
    max-width: 100%;
  }
`;

const ImageContainer = styled.div`
  display: flex;
  flex: 1;
  justify-content: flex-end;
  align-items: flex-start;

  svg {
    max-width: 45rem;
  }

  ${media('<=desktop')} {
    margin-top: 2rem;
    justify-content: center;
    svg {
      max-width: 80%;
    }
  }
`;

const Description = styled.p`
  font-size: 1.8rem;
  opacity: 0.8;
  line-height: 1.6;

  ${media('<=desktop')} {
    font-size: 1.5rem;
  }
`;

const CustomOverTitle = styled(OverTitle)`
  margin-bottom: 2rem;
`;

const Heading = styled.h1`
  font-size: 7.2rem;
  font-weight: bold;
  line-height: 1.1;
  margin-bottom: 4rem;
  letter-spacing: -0.03em;

  ${media('<=tablet')} {
    font-size: 4.6rem;
    margin-bottom: 2rem;
  }
`;
