import { CloudProvider, ProviderConfig } from './cloud';

export interface ExportRequest {
  uri?: string;
  cluster?: string;
  username?: string;
  password?: string;
  db: string;
  collection: string;
}

export interface BackupRequest extends ExportRequest {
  provider: CloudProvider;
  dest_path: string;
  provider_config?: ProviderConfig;
}

export interface ScheduleRequest extends BackupRequest {
  job_id: string;
  cron_expression: string;
}
