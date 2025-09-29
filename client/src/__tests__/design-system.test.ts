/**
 * Design System Tests
 * Tests for corporate design system implementation
 * Based on folio-parse-stream reference patterns
 */

import { describe, it, expect, beforeEach } from 'vitest';

describe('Design System - CSS Custom Properties', () => {
  let testElement: HTMLDivElement;

  beforeEach(() => {
    // Create a test element to check computed styles
    testElement = document.createElement('div');
    document.body.appendChild(testElement);
  });

  afterEach(() => {
    document.body.removeChild(testElement);
  });

  it('should have corporate primary color defined', () => {
    const computedStyle = getComputedStyle(document.documentElement);
    const primaryColor = computedStyle.getPropertyValue('--primary').trim();

    // Corporate brown: 25 45% 15%
    expect(primaryColor).toBe('25 45% 15%');
  });

  it('should have accent color defined', () => {
    const computedStyle = getComputedStyle(document.documentElement);
    const accentColor = computedStyle.getPropertyValue('--accent').trim();

    // Premium bronze: 35 65% 45%
    expect(accentColor).toBe('35 65% 45%');
  });

  it('should have consistent border radius', () => {
    const computedStyle = getComputedStyle(document.documentElement);
    const radius = computedStyle.getPropertyValue('--radius').trim();

    // Enhanced border radius: 0.75rem
    expect(radius).toBe('0.75rem');
  });

  it('should have professional shadow definitions', () => {
    const computedStyle = getComputedStyle(document.documentElement);
    const shadowSoft = computedStyle.getPropertyValue('--shadow-soft').trim();
    const shadowMedium = computedStyle.getPropertyValue('--shadow-medium').trim();
    const shadowStrong = computedStyle.getPropertyValue('--shadow-strong').trim();

    expect(shadowSoft).toContain('0 2px 8px -2px');
    expect(shadowMedium).toContain('0 4px 16px -4px');
    expect(shadowStrong).toContain('0 8px 32px -8px');
  });

  it('should have corporate gradient definitions', () => {
    const computedStyle = getComputedStyle(document.documentElement);
    const gradientPrimary = computedStyle.getPropertyValue('--gradient-primary').trim();
    const gradientAccent = computedStyle.getPropertyValue('--gradient-accent').trim();

    expect(gradientPrimary).toContain('linear-gradient');
    expect(gradientPrimary).toContain('hsl(25 45% 15%)');
    expect(gradientAccent).toContain('linear-gradient');
    expect(gradientAccent).toContain('hsl(35 65% 45%)');
  });
});

describe('Design System - Typography', () => {
  it('should have consistent font size scale', () => {
    const computedStyle = getComputedStyle(document.documentElement);

    expect(computedStyle.getPropertyValue('--font-size-xs').trim()).toBe('0.75rem');
    expect(computedStyle.getPropertyValue('--font-size-sm').trim()).toBe('0.875rem');
    expect(computedStyle.getPropertyValue('--font-size-base').trim()).toBe('1rem');
    expect(computedStyle.getPropertyValue('--font-size-lg').trim()).toBe('1.125rem');
    expect(computedStyle.getPropertyValue('--font-size-xl').trim()).toBe('1.25rem');
  });

  it('should have consistent spacing scale', () => {
    const computedStyle = getComputedStyle(document.documentElement);

    expect(computedStyle.getPropertyValue('--space-1').trim()).toBe('0.25rem');
    expect(computedStyle.getPropertyValue('--space-2').trim()).toBe('0.5rem');
    expect(computedStyle.getPropertyValue('--space-4').trim()).toBe('1rem');
    expect(computedStyle.getPropertyValue('--space-8').trim()).toBe('2rem');
  });
});

describe('Design System - Accessibility', () => {
  it('should have proper focus styles defined', () => {
    const testInput = document.createElement('input');
    testInput.setAttribute('data-testid', 'focus-test');
    document.body.appendChild(testInput);

    testInput.focus();
    const computedStyle = getComputedStyle(testInput, ':focus-visible');

    // Should have focus outline defined
    expect(computedStyle.getPropertyValue('outline-width')).toBe('2px');
    expect(computedStyle.getPropertyValue('outline-offset')).toBe('2px');

    document.body.removeChild(testInput);
  });

  it('should have smooth scroll behavior enabled', () => {
    const htmlStyle = getComputedStyle(document.documentElement);
    expect(htmlStyle.getPropertyValue('scroll-behavior')).toBe('smooth');
  });
});

describe('Design System - Dark Mode Support', () => {
  beforeEach(() => {
    // Add dark class to test dark mode variables
    document.documentElement.classList.add('dark');
  });

  afterEach(() => {
    // Remove dark class after test
    document.documentElement.classList.remove('dark');
  });

  it('should have dark mode color definitions', () => {
    const computedStyle = getComputedStyle(document.documentElement);

    // In dark mode, background should be darker
    const darkBackground = computedStyle.getPropertyValue('--background').trim();
    expect(darkBackground).toBe('25 25% 8%');

    // Foreground should be lighter in dark mode
    const darkForeground = computedStyle.getPropertyValue('--foreground').trim();
    expect(darkForeground).toBe('25 15% 92%');
  });

  it('should maintain proper contrast in dark mode', () => {
    const computedStyle = getComputedStyle(document.documentElement);

    // Dark mode should have adjusted shadow values
    const darkShadowSoft = computedStyle.getPropertyValue('--shadow-soft').trim();
    expect(darkShadowSoft).toContain('hsl(0 0% 0% / 0.2)');
  });
});

describe('Design System - Status Colors', () => {
  it('should have accessible status color definitions', () => {
    const computedStyle = getComputedStyle(document.documentElement);

    // Success green
    expect(computedStyle.getPropertyValue('--success').trim()).toBe('145 65% 42%');

    // Warning amber
    expect(computedStyle.getPropertyValue('--warning').trim()).toBe('35 85% 55%');

    // Destructive red
    expect(computedStyle.getPropertyValue('--destructive').trim()).toBe('0 75% 55%');

    // Info blue
    expect(computedStyle.getPropertyValue('--info').trim()).toBe('220 70% 50%');
  });

  it('should have proper foreground colors for status backgrounds', () => {
    const computedStyle = getComputedStyle(document.documentElement);

    // All status colors should have white foreground for proper contrast
    expect(computedStyle.getPropertyValue('--success-foreground').trim()).toBe('0 0% 98%');
    expect(computedStyle.getPropertyValue('--warning-foreground').trim()).toBe('25 25% 12%');
    expect(computedStyle.getPropertyValue('--destructive-foreground').trim()).toBe('0 0% 98%');
    expect(computedStyle.getPropertyValue('--info-foreground').trim()).toBe('0 0% 98%');
  });
});

describe('Design System - Animation & Transitions', () => {
  it('should have consistent transition timing functions', () => {
    const computedStyle = getComputedStyle(document.documentElement);

    const transitionSmooth = computedStyle.getPropertyValue('--transition-smooth').trim();
    const transitionFast = computedStyle.getPropertyValue('--transition-fast').trim();

    expect(transitionSmooth).toContain('0.3s cubic-bezier(0.4, 0, 0.2, 1)');
    expect(transitionFast).toContain('0.15s cubic-bezier(0.4, 0, 0.2, 1)');
  });
});