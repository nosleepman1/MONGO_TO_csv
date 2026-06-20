import { CloudProvider } from './cloud';

export interface BaseResponse {
  status: 'success' | 'error';
  message?: string;
}

export interface BackupResponse extends BaseResponse {
  message: string;
}

export interface SchedulerStatusResponse {
  status: 'success';
  running: boolean;
}

export interface ScheduleResponse extends BaseResponse {
  message: string;
}

export interface JobArgs {
  db_name: string;
  collection_name: string;
  provider: CloudProvider;
  dest_path: string;
}

export interface Job {
  id: string;
  next_run_time: string | null; // ISO string format or null if paused
  cron_expression: string;
  args: JobArgs;
  kwargs: {
    mongo_uri: string; // Will be "[SÉCURISÉ]"
    connection_details: string; // Will be "[SÉCURISÉ]"
    provider_config: string; // Will be "[SÉCURISÉ]"
  };
}

export interface JobsListResponse {
  status: 'success';
  jobs: Job[];
}

export interface DeleteJobResponse extends BaseResponse {
  message: string;
}

export interface ApiError {
  detail: string | Array<{
    loc: (string | number)[];
    msg: string;
    type: string;
  }>;
}
