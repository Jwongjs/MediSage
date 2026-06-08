import React, { PropsWithChildren } from 'react';
import styled from 'styled-components';
import Container from './Container';
import OverTitle from './OverTitle';
import RichText from 'components/RichText';
import { media } from 'utils/media'; 

export interface BasicSectionProps {
  imageUrl: string;
  title: string;
  overTitle: string;
  reversed?: boolean;
}

export default function BasicSection({
  imageUrl,
  title,
  overTitle,
  reversed,
  children,
}: PropsWithChildren<BasicSectionProps>) {
  return (
    <BasicSectionWrapper reversed={reversed}>
      <ImageContainer>
        <StyledImage src={imageUrl} alt={title} />
      </ImageContainer>
      <ContentContainer>
        <CustomOverTitle>{overTitle}</CustomOverTitle>
        <Title>{title}</Title>
        <RichText>{children}</RichText>
      </ContentContainer>
    </BasicSectionWrapper>
  );
}

// Styled Components
const Title = styled.h1`
  font-size: 5.2rem;
  font-weight: bold;
  line-height: 1.1;
  margin-bottom: 4rem;
  letter-spacing: -0.03em;

  ${media('<=tablet')} {
    font-size: 4.6rem;
    margin-bottom: 2rem;
  }
`;

const CustomOverTitle = styled(OverTitle)`
  margin-bottom: 2rem;
`;

const ImageContainer = styled.div`
  flex: 1;
  position: relative;
  width: 100%;
  max-width: 600px;

  ${media('<=desktop')} {
    width: 100%;
    margin-bottom: 2.5rem;
  }
`;

const StyledImage = styled.img`
  width: 100%;
  height: auto;
  border-radius: 0.6rem;
  object-fit: cover;
`;

const ContentContainer = styled.div`
  flex: 1;
`;

type Props = Pick<BasicSectionProps, 'reversed'>;

const BasicSectionWrapper = styled(Container)<Props>`
  display: flex;
  align-items: center;
  flex-direction: ${(p) => (p.reversed ? 'row-reverse' : 'row')};

  ${ImageContainer} {
    margin: ${(p) => (p.reversed ? '0 0 0 5rem' : '0 5rem 0 0')};
  }

  ${media('<=desktop')} {
    flex-direction: column;

    ${ImageContainer} {
      margin: 0 0 2.5rem 0;
    }
  }
`;
