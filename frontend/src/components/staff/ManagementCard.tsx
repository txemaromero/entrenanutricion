import {
  IonButton,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardSubtitle,
  IonCardTitle,
  IonFab,
  IonFabButton,
  IonIcon,
  IonSearchbar,
} from '@ionic/react';
import { add, createOutline, eyeOutline, personAddOutline, trashOutline } from 'ionicons/icons';
import { useEffect, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

interface ManagementCardProps {
  title: string;
  subtitle?: string;
  description?: string;
  children?: ReactNode;
  testId?: string;
  viewHref?: string;
  editHref?: string;
  onDelete?: () => void;
  onAssign?: () => void;
}

/** List card with View, Edit (green), Delete (red) and optional Assign (purple) actions. */
export const ManagementCard = ({
  title,
  subtitle,
  description,
  children,
  testId,
  viewHref,
  editHref,
  onDelete,
  onAssign,
}: ManagementCardProps) => {
  const { t } = useTranslation();
  return (
    <IonCard data-testid={testId}>
      <IonCardHeader>
        {subtitle && <IonCardSubtitle>{subtitle}</IonCardSubtitle>}
        <IonCardTitle style={{ fontSize: '1.1rem' }}>{title}</IonCardTitle>
      </IonCardHeader>
      <IonCardContent className="stack">
        {description && (
          <p className="muted" style={{ margin: 0 }}>
            {description}
          </p>
        )}
        {children}
        <div className="row row--wrap">
          {viewHref && (
            <IonButton size="small" fill="outline" routerLink={viewHref} data-testid="action-view">
              <IonIcon slot="start" icon={eyeOutline} aria-hidden="true" />
              {t('common.view')}
            </IonButton>
          )}
          {onAssign && (
            <IonButton size="small" color="tertiary" onClick={onAssign} data-testid="action-assign">
              <IonIcon slot="start" icon={personAddOutline} aria-hidden="true" />
              {t('common.assign')}
            </IonButton>
          )}
          {editHref && (
            <IonButton
              size="small"
              color={onAssign ? 'medium' : 'primary'}
              routerLink={editHref}
              data-testid="action-edit"
            >
              <IonIcon slot="start" icon={createOutline} aria-hidden="true" />
              {t('common.edit')}
            </IonButton>
          )}
          {onDelete && (
            <IonButton size="small" color="danger" onClick={onDelete} data-testid="action-delete">
              <IonIcon slot="start" icon={trashOutline} aria-hidden="true" />
              {t('common.delete')}
            </IonButton>
          )}
        </div>
      </IonCardContent>
    </IonCard>
  );
};

/** Search box that reports the query after the user stops typing. */
export const SearchBox = ({
  onSearch,
  testId,
}: {
  onSearch: (query: string) => void;
  testId?: string;
}) => {
  const { t } = useTranslation();
  const [value, setValue] = useState('');
  useEffect(() => {
    const id = setTimeout(() => onSearch(value.trim()), 300);
    return () => clearTimeout(id);
  }, [value, onSearch]);
  return (
    <IonSearchbar
      value={value}
      placeholder={t('common.search')}
      aria-label={t('common.search')}
      onIonInput={(event) => setValue(event.detail.value ?? '')}
      data-testid={testId ?? 'search'}
    />
  );
};

/** Floating "+" button for creating items. */
export const AddFab = ({ href, label }: { href: string; label: string }) => (
  <IonFab slot="fixed" vertical="bottom" horizontal="end">
    <IonFabButton routerLink={href} aria-label={label} data-testid="fab-add">
      <IonIcon icon={add} aria-hidden="true" />
    </IonFabButton>
  </IonFab>
);
