export interface Notification {
  id: string;
  ticket_id: string | null;
  event_type: string;
  title: string;
  body: string;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  total: number;
  page: number;
  page_size: number;
  unread_count: number;
  items: Notification[];
}

export interface NotificationPreference {
  event_type: string;
  in_app_enabled: boolean;
  email_enabled: boolean;
}

export interface NotificationPreferencesResponse {
  preferences: NotificationPreference[];
}

export interface NotificationPreferencesPatch {
  preferences: NotificationPreference[];
}
