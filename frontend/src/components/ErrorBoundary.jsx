// Owner: Ranjith
// Catches render crashes so a patient never sees a blank screen or a trace.

import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { crashed: false };
  }

  static getDerivedStateFromError() {
    return { crashed: true };
  }

  componentDidCatch(error, info) {
    // Detail goes to the console for staff/dev, never to the screen.
    console.error('[kiosk] render crash:', error, info);
  }

  reset = () => {
    this.setState({ crashed: false });
    this.props.onReset?.();
  };

  render() {
    if (this.state.crashed) return this.props.fallback(this.reset);
    return this.props.children;
  }
}
