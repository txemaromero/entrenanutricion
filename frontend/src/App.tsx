import { IonApp, IonRouterOutlet, setupIonicReact } from '@ionic/react';
import { IonReactRouter } from '@ionic/react-router';
import { Suspense } from 'react';
import { Redirect, Route } from 'react-router-dom';

import '@ionic/react/css/core.css';
import '@ionic/react/css/normalize.css';
import '@ionic/react/css/structure.css';
import '@ionic/react/css/typography.css';
import '@ionic/react/css/padding.css';
import '@ionic/react/css/flex-utils.css';
import '@ionic/react/css/display.css';
import '@ionic/react/css/palettes/dark.system.css';
import './theme/variables.css';
import './theme/global.css';

import { AuthProvider } from './auth/AuthContext';
import { useAuth } from './auth/useAuth';
import { PATHS, homePath } from './auth/routing';
import { FullPageSpinner } from './components/FullPageSpinner';
import { TabsLayout } from './layouts/TabsLayout';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import ResetPasswordPage from './pages/auth/ResetPasswordPage';
import PrivacyPolicyPage from './pages/shared/PrivacyPolicyPage';
import VerifyEmailPage from './pages/auth/VerifyEmailPage';
import { ConsentModal } from './components/privacy/ConsentModal';
import WelcomePage from './pages/auth/WelcomePage';
import OnboardingPage from './pages/client/OnboardingPage';

// Page transitions and other animations are off for people who ask for reduced motion.
const prefersReducedMotion =
  typeof window !== 'undefined' &&
  typeof window.matchMedia === 'function' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

setupIonicReact({ mode: 'md', animated: !prefersReducedMotion });

export const AppRoutes = () => {
  const { user, initializing } = useAuth();
  if (initializing) return <FullPageSpinner />;
  const home = homePath(user);

  return (
    <IonReactRouter>
      <IonRouterOutlet>
        <Route
          exact
          path={PATHS.welcome}
          render={() => (user ? <Redirect to={home} /> : <WelcomePage />)}
        />
        <Route
          exact
          path={PATHS.login}
          render={() => (user ? <Redirect to={home} /> : <LoginPage />)}
        />
        <Route
          exact
          path={PATHS.register}
          render={() => (user ? <Redirect to={home} /> : <RegisterPage />)}
        />
        <Route
          exact
          path={PATHS.forgotPassword}
          render={() => (user ? <Redirect to={home} /> : <ForgotPasswordPage />)}
        />
        <Route
          exact
          path={PATHS.resetPassword}
          render={() => (user ? <Redirect to={home} /> : <ResetPasswordPage />)}
        />
        {/* Public for everyone, signed in or not. */}
        <Route exact path={PATHS.privacy} render={() => <PrivacyPolicyPage />} />
        <Route exact path={PATHS.verifyEmail} render={() => <VerifyEmailPage />} />
        <Route
          exact
          path={PATHS.onboarding}
          render={() =>
            home === PATHS.onboarding ? (
              <OnboardingPage />
            ) : (
              <Redirect to={user ? home : PATHS.login} />
            )
          }
        />
        <Route
          path="/app"
          render={() =>
            user && home !== PATHS.onboarding ? (
              <TabsLayout user={user} />
            ) : (
              <Redirect to={user ? home : PATHS.login} />
            )
          }
        />
        <Route render={() => <Redirect to={home} />} />
      </IonRouterOutlet>
      <ConsentModal />
    </IonReactRouter>
  );
};

const App = () => (
  <IonApp>
    <Suspense fallback={<FullPageSpinner />}>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Suspense>
  </IonApp>
);

export default App;
