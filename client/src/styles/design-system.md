# Information Extraction Platform - Design System

## Overview

This design system is inspired by Sanabil's professional corporate aesthetic, enhanced for accessibility and modern design patterns. It provides a comprehensive set of design tokens, components, and utilities for building consistent, accessible user interfaces.

## Corporate Branding

### Color Palette

#### Primary Colors (Corporate Brown)
- `--primary: 25 45% 15%` - Deep corporate brown (Sanabil brand)
- `--primary-foreground: 0 0% 98%` - White text on primary
- `--primary-hover: 25 45% 20%` - Hover state for primary

#### Accent Colors (Premium Bronze)
- `--accent: 35 65% 45%` - Bronze/gold accent
- `--accent-foreground: 0 0% 98%` - White text on accent
- `--accent-subtle: 35 35% 95%` - Light bronze background

#### Status Colors
- `--success: 145 65% 42%` - Green for success states
- `--warning: 35 85% 55%` - Amber for warning states
- `--destructive: 0 75% 55%` - Red for error states
- `--info: 220 70% 50%` - Blue for informational states

### Typography Scale

- `--font-size-xs: 0.75rem` (12px)
- `--font-size-sm: 0.875rem` (14px)
- `--font-size-base: 1rem` (16px)
- `--font-size-lg: 1.125rem` (18px)
- `--font-size-xl: 1.25rem` (20px)
- `--font-size-2xl: 1.5rem` (24px)
- `--font-size-3xl: 1.875rem` (30px)
- `--font-size-4xl: 2.25rem` (36px)

### Spacing Scale

- `--space-1: 0.25rem` (4px)
- `--space-2: 0.5rem` (8px)
- `--space-3: 0.75rem` (12px)
- `--space-4: 1rem` (16px)
- `--space-6: 1.5rem` (24px)
- `--space-8: 2rem` (32px)
- `--space-12: 3rem` (48px)
- `--space-16: 4rem` (64px)

## Gradients

### Corporate Gradients
- `gradient-primary` - Primary corporate brown gradient
- `gradient-accent` - Premium bronze accent gradient
- `gradient-subtle` - Subtle background gradient
- `gradient-hero` - Hero section gradient

## Shadows

### Professional Shadows
- `shadow-soft` - Subtle depth for cards and components
- `shadow-medium` - Standard elevation for modals and dropdowns
- `shadow-strong` - Maximum elevation for overlays
- `shadow-glow` - Accent glow effect for highlights

## Animations

### Timing Functions
- `transition-smooth` - Smooth, professional transitions (300ms)
- `transition-fast` - Quick feedback transitions (150ms)
- `transition-bounce` - Playful bounce effect

### Keyframes
- `fade-in` - Smooth opacity transition
- `slide-up` - Content entrance animation
- `pulse-glow` - Accent highlighting animation

## Accessibility Features

### Focus Management
- Enhanced focus indicators with 2px outline
- High contrast focus states for keyboard navigation
- Proper focus offset for visual clarity

### Color Contrast
- All color combinations meet WCAG 2.1 AA standards
- Status colors optimized for accessibility
- Dark mode support with proper contrast ratios

### Typography
- Consistent line heights for readability
- Appropriate letter spacing for professional text
- Font feature settings enabled for enhanced legibility

## Usage Examples

### CSS Custom Properties
```css
.corporate-button {
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
  transition: var(--transition-smooth);
}

.corporate-button:hover {
  background: hsl(var(--primary-hover));
}
```

### Tailwind Classes
```jsx
<div className="bg-gradient-primary text-primary-foreground shadow-soft transition-smooth">
  Corporate styled component
</div>
```

### Typography Classes
```jsx
<h1 className="text-corporate text-4xl">Corporate Heading</h1>
<p className="text-accent-corporate">Accent text</p>
```

## Component Guidelines

### Cards
- Use `shadow-soft` for standard cards
- Apply `shadow-medium` for hover states
- Corporate brown borders with `border-border`

### Buttons
- Primary buttons use `gradient-primary`
- Accent buttons use `gradient-accent`
- Ghost buttons for subtle actions

### Forms
- Consistent input styling with `border-input`
- Focus states with `ring-ring`
- Error states with `destructive` colors

## Dark Mode Support

The design system includes comprehensive dark mode support with:
- Adjusted color values for dark backgrounds
- Enhanced contrast for readability
- Consistent visual hierarchy in both modes

## Best Practices

1. **Consistency**: Use design tokens consistently across all components
2. **Accessibility**: Always test color contrast and keyboard navigation
3. **Performance**: Leverage CSS custom properties for efficient theming
4. **Maintainability**: Document custom implementations and variations
5. **Testing**: Validate design system changes across all components

## Migration from Default Theme

When migrating from the default shadcn/ui theme:
1. Update color references to use corporate palette
2. Apply consistent shadow and gradient usage
3. Test all components with new theme
4. Validate accessibility compliance
5. Update documentation and style guides