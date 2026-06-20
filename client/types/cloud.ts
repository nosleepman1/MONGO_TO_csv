export type CloudProvider = 's3' | 'dropbox' | 'gdrive' | 'mock';

export interface S3Config {
  aws_access_key_id?: string;
  aws_secret_access_key?: string;
  region_name?: string;
  bucket_name: string;
}

export interface DropboxConfig {
  access_token: string;
}

export interface GDriveConfig {
  credentials_file?: string;
  folder_id?: string;
}

export type ProviderConfig = S3Config | DropboxConfig | GDriveConfig | Record<string, never>;
