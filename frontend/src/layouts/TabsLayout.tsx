import {
  IonButton,
  IonIcon,
  IonLabel,
  IonRouterOutlet,
  IonTabBar,
  IonTabButton,
  IonTabs,
} from '@ionic/react';
import {
  barbellOutline,
  fitnessOutline,
  hourglassOutline,
  peopleOutline,
  personCircleOutline,
  personAddOutline,
  pieChartOutline,
  restaurantOutline,
  statsChartOutline,
  trendingUpOutline,
} from 'ionicons/icons';
import { useTranslation } from 'react-i18next';
import { Redirect, Route } from 'react-router-dom';

import type { Me } from '../api/types';
import { homePath, tabsFor, type TabKey } from '../auth/routing';
import { FullPageSpinner } from '../components/FullPageSpinner';
import { useOfflineSync } from '../offline/useOfflineSync';
import { useRoleRoutes } from './useRoleRoutes';

const ICONS: Record<TabKey, string> = {
  status: hourglassOutline,
  training: barbellOutline,
  nutrition: pieChartOutline,
  progress: trendingUpOutline,
  profile: personCircleOutline,
  catalog: fitnessOutline,
  mealPlans: restaurantOutline,
  users: peopleOutline,
  assignments: personAddOutline,
  statistics: statsChartOutline,
};

/**
 * Bottom tab bar with icon + text. IonTabs selects exactly one tab from the current URL
 * (tab paths never prefix each other), fixing the "several tabs highlighted" bug.
 */
export const TabsLayout = ({ user }: { user: Me }) => {
  const { t } = useTranslation();
  const tabs = tabsFor(user);
  const { routes, failed } = useRoleRoutes(user);
  useOfflineSync(user.role === 'client');
  const home = homePath(user);

  if (failed) {
    // Usually a new version was deployed and the old page files are gone: reload the app.
    return (
      <div className="stack" style={{ padding: 24, textAlign: 'center' }} role="alert">
        <p>{t('states.appLoadFailed')}</p>
        <IonButton onClick={() => window.location.reload()}>{t('states.reload')}</IonButton>
      </div>
    );
  }
  if (!routes) return <FullPageSpinner />;

  return (
    <IonTabs>
      <IonRouterOutlet>
        {routes.map((route) => (
          <Route
            key={route.path}
            path={route.path}
            exact={route.exact}
            component={route.component}
          />
        ))}
        <Route exact path="/app" render={() => <Redirect to={home} />} />
        <Route render={() => <Redirect to={home} />} />
      </IonRouterOutlet>
      <IonTabBar
        slot="bottom"
        data-testid="tab-bar"
        className={tabs.length > 4 ? 'tab-bar--dense' : undefined}
      >
        {tabs.map((tab) => (
          <IonTabButton key={tab.key} tab={tab.key} href={tab.path} data-testid={`tab-${tab.key}`}>
            <IonIcon icon={ICONS[tab.key]} aria-hidden="true" />
            <IonLabel>{t(tab.labelKey)}</IonLabel>
          </IonTabButton>
        ))}
      </IonTabBar>
    </IonTabs>
  );
};
