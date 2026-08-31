---
layout: post
title: "Contact"
categories: Contact
order: 1
---
<p class="lead text-secondary">Connect with Arbyte for embedded systems training, course previews, partnerships, and technical enquiries.</p>

<div class="row g-4 mb-5">
  <div class="col-md-6">
    <div class="card contact-card h-100 border-0 bg-light">
      <div class="card-body p-4">
        <span class="section-kicker">Call us</span>
        <h2 class="h5 mt-2">Training enquiries</h2>
        <a class="contact-link" href="tel:+919500459614">+91 95004 59614</a>
      </div>
    </div>
  </div>
  <div class="col-md-6">
    <div class="card contact-card h-100 border-0 bg-light">
      <div class="card-body p-4">
        <span class="section-kicker">Email us</span>
        <h2 class="h5 mt-2">General enquiries</h2>
        <a class="contact-link" href="mailto:info@arbyte.dev">info@arbyte.dev</a>
      </div>
    </div>
  </div>
</div>

## Our locations

<div class="row g-4 mb-5">
  <div class="col-md-4">
    <div class="card location-card h-100">
      <div class="card-body p-4">
        <span class="location-badge">Country</span>
        <h3 class="h5 mt-3">India</h3>
        <p class="text-secondary mb-0">Primary operating country for Arbyte training programs and engineering services.</p>
      </div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="card location-card h-100">
      <div class="card-body p-4">
        <span class="location-badge">Regional presence</span>
        <h3 class="h5 mt-3">Tamil Nadu</h3>
        <p class="text-secondary mb-0">Serving learners and engineering teams throughout Tamil Nadu.</p>
      </div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="card location-card h-100">
      <div class="card-body p-4">
        <span class="location-badge">Sub-branch</span>
        <h3 class="h5 mt-3">Coimbatore</h3>
        <p class="text-secondary mb-1">Coimbatore, Tamil Nadu, India</p>
        <p class="small text-muted mb-0">Detailed branch address and visiting hours will be announced soon.</p>
      </div>
    </div>
  </div>
</div>

## Training programs and previews

<div class="card training-link-card border-0 mb-5">
  <div class="card-body p-4 d-md-flex align-items-center justify-content-between gap-4">
    <div>
      <h3 class="h5">Arbyte training preview repository</h3>
      <p class="text-secondary mb-md-0">Explore preview material and updates for practical embedded training programs.</p>
    </div>
    <a class="btn btn-primary flex-shrink-0" href="{{ site.training_preview_url }}" target="_blank" rel="noopener noreferrer">View course previews on GitHub</a>
  </div>
</div>

## Connect with Arbyte

<p class="text-secondary">Official GitHub is available now. Other social channels are reserved as placeholders and will be updated when their Arbyte profiles launch.</p>

<div class="social-grid mb-3">
  {% for social in site.data.social_links %}
    {% if social.status == "active" %}
      <a class="social-link-card" href="{{ social.url }}" target="_blank" rel="noopener noreferrer" aria-label="Arbyte on {{ social.name }}">
        <span class="social-monogram" aria-hidden="true">{{ social.name | slice: 0 }}</span>
        <span><strong>{{ social.name }}</strong><small>Visit profile</small></span>
      </a>
    {% else %}
      <div class="social-link-card social-link-card--placeholder" aria-label="Arbyte on {{ social.name }} (coming soon)">
        <span class="social-monogram" aria-hidden="true">{{ social.name | slice: 0 }}</span>
        <span><strong>{{ social.name }}</strong><small>Profile coming soon</small></span>
      </div>
    {% endif %}
  {% endfor %}
</div>
