import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { media } from 'utils/media'; 

export interface ArticleCardProps {
  title: string;
  slug: string;
  imageUrl: string;
  description: string;
}

export default function ArticleCard({ title, slug, imageUrl, description }: ArticleCardProps) {
  return (
    <StyledLink to={'/blog/' + slug}>
      <ArticleCardWrapper className="article-card-wrapper">
        <HoverEffectContainer>
          <ImageContainer>
            <img src={imageUrl} alt={title} />
          </ImageContainer>
          <Content>
            <Title>{title}</Title>
            <Description>{description}</Description>
          </Content>
        </HoverEffectContainer>
      </ArticleCardWrapper>
    </StyledLink>
  );
}

// Use styled(Link) instead of <a> when using react-router-dom
const StyledLink = styled(Link)`
  text-decoration: none;
  color: inherit;
`;

const ArticleCardWrapper = styled.div`
  display: flex;
  flex-direction: column;
  height: 45rem;
  max-width: 35rem;
  overflow: hidden;
  text-decoration: none;
  border-radius: 0.6rem;
  background: rgb(var(--cardBackground));
  cursor: pointer;
  color: rgb(var(--text));
`;

const HoverEffectContainer = styled.div`
  transition: transform 0.3s;
  backface-visibility: hidden;
  will-change: transform;

  &:hover {
    border-radius: 0.6rem;
    overflow: hidden;
    transform: scale(1.025);
  }
`;

const ImageContainer = styled.div`
  position: relative;
  height: 20rem;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 0.6rem 0.6rem 0 0;
  }

  ${media('<=desktop')} {
    width: 100%;
  }
`;

const Content = styled.div`
  padding: 0 2rem;

  & > * {
    margin-top: 2rem;
  }
`;

const Title = styled.h4`
  font-size: 1.8rem;

  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
`;

const Description = styled.p`
  font-size: 1.6rem;

  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  opacity: 0.6;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 5;
`;