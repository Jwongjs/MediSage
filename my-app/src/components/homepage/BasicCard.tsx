import styled from 'styled-components';

interface BasicCardProps {
  title: string;
  description: string;
  imageUrl: string;
}

const Card = styled.div`
  padding: 16px;
  border: 1px solid #eee;
  border-radius: 8px;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const Title = styled.h2`
  margin: 12px 0 8px 0;
  font-size: 1.25rem;
  font-weight: bold;
`;

const Description = styled.p`
  color: #555;
  font-size: 1rem;
  text-align: center;
`;

interface BasicCardProps {
  title: string;
  description: string;
  imageUrl: string;
}

export default function BasicCard({ title, description, imageUrl }: BasicCardProps) {
  return (
    <Card>
      <img src={imageUrl} width={128} height={128} alt={title} />
      <Title>{title}</Title>
      <Description>{description}</Description>
    </Card>
  );
}
