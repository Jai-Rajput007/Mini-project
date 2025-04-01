import React from 'react';
import styled from 'styled-components';
import { useState,useEffect } from 'react';
interface SocialsProps {
  className?: string;
}

export const Socials: React.FC<SocialsProps> = ({ className }) => {

  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <StyledWrapper className={className}>
    <div className="card">
      <span>Socials</span>
      <a className="social-link" href="https://github.com/Jai-Rajput007" target="_blank" rel="noopener noreferrer">
        <img src="/github.svg" alt="Github" />
      </a>
      <a className="social-link" href="https://www.linkedin.com/in/j-s-rajput/" target="_blank" rel="noopener noreferrer">
        <img src="/Linkedin.svg" alt="Linkedin" style={{ width: '24px', height: '24px' }} />
      </a>
      <a className="social-link" href="https://www.reddit.com/user/North-Philosophy-846/" target="_blank" rel="noopener noreferrer">
        <img src="/Reddit.svg" alt="Reddit" style={{ width: '24px', height: '24px' }} />
      </a>
      <a className="social-link" href="https://medium.com/@Jai_s_Rajput" target="_blank" rel="noopener noreferrer">
        <img src="/Medium.svg" alt="Medium" style={{ width: '24px', height: '24px' }} />
      </a>
    </div>
  </StyledWrapper>
  );
};

interface StyledWrapperProps {
  className?: string;
}

const StyledWrapper = styled.div<StyledWrapperProps>`
  .card svg {
    height: 25px;
  }

  .card {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #e7e7e7;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    overflow: hidden;
    height: 50px;
    width: 200px;
  }

  .card::before, .card::after {
    position: absolute;
    display: flex;
    align-items: center;
    width: 50%;
    height: 100%;
    transition: 0.25s linear;
    z-index: 1;
  }

  .card::before {
    content: "";
    left: 0;
    justify-content: flex-end;
    background-color: #4d60b6;
  }

  .card::after {
    content: "";
    right: 0;
    justify-content: flex-start;
    background-color: #4453a6;
  }

  .card:hover {
    box-shadow: 0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22);
  }

  .card:hover span {
    opacity: 0;
    z-index: -3;
  }

  .card:hover::before {
    opacity: 0.5;
    transform: translateY(-100%);
  }

  .card:hover::after {
    opacity: 0.5;
    transform: translateY(100%);
  }

  .card span {
    position: absolute;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    color: whitesmoke;
    font-family: 'Fira Mono', monospace;
    font-size: 24px;
    font-weight: 700;
    opacity: 1;
    transition: opacity 0.25s;
    z-index: 2;
  }

  .card .social-link {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 25%;
    height: 100%;
    color: whitesmoke;
    font-size: 24px;
    text-decoration: none;
    transition: 0.25s;
  }

  .card .social-link svg {
    text-shadow: 1px 1px rgba(31, 74, 121, 0.7);
    transform: scale(1);
  }

  .card .social-link:hover {
    background-color: rgba(249, 244, 255, 0.774);
    animation: bounce_613 0.4s linear;
  }

  @keyframes bounce_613 {
    40% {
      transform: scale(1.4);
    }

    60% {
      transform: scale(0.8);
    }

    80% {
      transform: scale(1.2);
    }

    100% {
      transform: scale(1);
    }
  }
`;

export default Socials;