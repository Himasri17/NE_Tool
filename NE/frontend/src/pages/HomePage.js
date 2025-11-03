// src/pages/HomePage/HomePage.js
import React from 'react';
import { useNavigate } from 'react-router-dom';
import './HomePage.css'; // If you're using the CSS version

const HomePage = () => {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate('/login');
  };

  const FeatureCard = ({ icon, title }) => (
    <div className="feature-card">
      <div className="feature-icon">{icon}</div>
      <h3 className="feature-title">{title}</h3>
    </div>
  );

  return (
    <div className="home-page">
      {/* App Bar */}
      <header className="app-bar">
        <div className="app-bar-content">
          <div className="logo-container">
            <img 
              src="/logo.png" 
              alt="Logo" 
              className="logo"
            />
          </div>
          
          <button
            onClick={handleGetStarted}
            className="login-button"
          >
            <span>👤</span>
            Sign Up / Login
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-background">
          <div 
            className="background-image"
            style={{ backgroundImage: "url('/assets/images/institution.png')" }}
          ></div>
          <div className="gradient-overlay"></div>
        </div>
        
        <div className="hero-content">
          <div className="hero-text">
            <h1 className="hero-title">
              Indian Language Named Entity Annotation
            </h1>
            <p className="hero-subtitle">
              Named Entity Recognition (NER) is a vital task in Natural Language Processing (NLP), 
              helping machines identify and classify names, organizations, locations, dates, and numerical expressions. 
              These annotation guidelines provide a structured framework for Indian languages, ensuring accurate and 
              scalable dataset creation.
            </p>
            <button
              onClick={handleGetStarted}
              className="get-started-button"
            >
              Get Started
            </button>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section className="about-section">
        <div className="about-card">
          <h2 className="about-title">What is Named Entity Recognition?</h2>
          <p className="about-description">
            Named Entity Recognition (NER) is the process of identifying and categorizing entities in text. 
            This includes proper nouns (ENAMEX), numerical expressions (NUMEX), and temporal expressions (TIMEX). 
            Our annotation guidelines provide a structured approach to annotating these entities, ensuring 
            high-quality linguistic datasets for Indian languages.
          </p>
        </div>
      </section>

      {/* Key Features Section */}
      <section className="features-section">
        <h2 className="features-title">Key Features</h2>
        <div className="features-grid">
          <FeatureCard 
            icon="🏷️" 
            title="ENAMEX Entities" 
          />
          <FeatureCard 
            icon="🔢" 
            title="NUMEX Expressions" 
          />
          <FeatureCard 
            icon="⏰" 
            title="TIMEX Expressions" 
          />
          <FeatureCard 
            icon="🌐" 
            title="Indian Language Support" 
          />
          <FeatureCard 
            icon="✅" 
            title="High Accuracy" 
          />
        </div>
      </section>

      {/* Call to Action Section */}
      <section className="cta-section">
        <h2 className="cta-title">Ready to Start Annotating?</h2>
        <button
          onClick={handleGetStarted}
          className="cta-button"
        >
          Start Annotating Now
        </button>
      </section>

      {/* Footer */}
      <footer className="footer">
        <p className="footer-text">© 2025 NE Annotation Tool</p>
      </footer>
    </div>
  );
};

export default HomePage;