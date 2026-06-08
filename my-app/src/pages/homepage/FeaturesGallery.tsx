import React, { useState } from 'react';
import styled from 'styled-components';
import Collapse from 'components/homepage/Collapse';
import Container from 'components/homepage/Container';
import OverTitle from 'components/homepage/OverTitle';
import SectionTitle from 'components/homepage/SectionTitle';
import ThreeLayersCircle from 'components/homepage/ThreeLayersCircle';
import { media } from 'utils/media';

const TABS = [
  {
    title: 'Find relevant media contacts - multiline title',
    description:
      '<p>Lorem ipsum dolor sit amet consectetur adipisicing elit. Quibusdam quidem ipsam ratione dicta quis cupiditate consequuntur laborum ducimus iusto velit.</p>',
    imageUrl: '/demo-illustration-3.png',
    baseColor: '249,82,120',
    secondColor: '221,9,57',
  },
  {
    title: 'Another amazing feature',
    description:
      '<p>Lorem ipsum dolor sit amet consectetur adipisicing elit. Quibusdam quidem ipsam ratione dicta quis cupiditate consequuntur laborum ducimus iusto velit.</p>',
    imageUrl: '/demo-illustration-4.png',
    baseColor: '57,148,224',
    secondColor: '99,172,232',
  },
  {
    title: 'And yet... another truly fascinating feature',
    description:
      '<p>Lorem ipsum dolor sit amet consectetur adipisicing elit. Quibusdam quidem ipsam ratione dicta quis cupiditate consequuntur laborum ducimus iusto velit.</p>',
    imageUrl: '/demo-illustration-5.png',
    baseColor: '88,193,132',
    secondColor: '124,207,158',
  },
];

export default function FeaturesGallery() {
  const [currentTab, setCurrentTab] = useState(TABS[0]);

  const imagesMarkup = TABS.map((singleTab, idx) => {
    const isActive = singleTab.title === currentTab.title;
    return (
      <ImageContainer key={singleTab.title} isActive={isActive}>
        <img
          src={singleTab.imageUrl}
          alt={singleTab.title}
          style={{ width: '100%', height: '100%', objectFit: 'contain', position: 'absolute' }}
        />
      </ImageContainer>
    );
  });

  const tabsMarkup = TABS.map((singleTab, idx) => {
    const isActive = singleTab.title === currentTab.title;
    return (
      <Tab isActive={isActive} key={idx} onClick={() => setCurrentTab(TABS[idx])}>
        <TabTitleContainer>
          <CircleContainer>
            <ThreeLayersCircle
              baseColor={isActive ? 'transparent' : singleTab.baseColor}
              secondColor={singleTab.secondColor}
            />
          </CircleContainer>
          <h4>{singleTab.title}</h4>
        </TabTitleContainer>
        <Collapse isOpen={isActive} duration={300}>
          <TabContent>
            <div dangerouslySetInnerHTML={{ __html: singleTab.description }}></div>
          </TabContent>
        </Collapse>
      </Tab>
    );
  });

  return (
    <FeaturesGalleryWrapper>
      <Content>
        <OverTitle>features</OverTitle>
        <SectionTitle>What are you signing in for?</SectionTitle>
      </Content>
      <GalleryWrapper>
        <TabsContainer>{tabsMarkup}</TabsContainer>
        {imagesMarkup}
      </GalleryWrapper>
    </FeaturesGalleryWrapper>
  );
}

// Styled-components (unchanged)
const FeaturesGalleryWrapper = styled(Container)` ... `;
const GalleryWrapper = styled.div` ... `;
const Content = styled.div` ... `;
const TabsContainer = styled.div` ... `;
const ImageContainer = styled.div<{ isActive: boolean }>` ... `;
const Tab = styled.div<{ isActive: boolean }>` ... `;
const TabTitleContainer = styled.div` ... `;
const TabContent = styled.div` ... `;
const CircleContainer = styled.div` ... `;
