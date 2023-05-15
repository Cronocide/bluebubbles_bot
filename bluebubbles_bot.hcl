job "bbbot" {
	datacenters = ["atlas"]
	group "primary" {
		network {
			port "http" {
				static = "7487"
			}
		}
		service {
			name = "${NOMAD_JOB_NAME}-http"
			tags = ["http","internal","management","private"]
			port = "http"
                }
                volume "app" {
                        type = "csi"
                        source = "bbbot"
                        read_only = false
                        attachment_mode = "file-system"
                        access_mode = "single-node-writer"
                        per_alloc = false
                }
                task "prepare-volumes" {
                        driver = "docker"
                        config {
                                image = "busybox:latest"
                                command = "sh"
                                args = ["-c", "chown 1000:1000 /data"]
                        }
                        volume_mount {
                                volume = "app"
                                destination = "/data"
                                read_only = false
                        }
                        lifecycle {
                                hook = "prestart"
                                sidecar = false
                        }
                }
		task "server" {
			driver = "docker"
			config {
				image = "git.cronocide.net/cronocide/bluebubbles-bot:latest"
				image_pull_timeout = "15m"
				ports = ["http"]
			}
			volume_mount {
				volume = "app"
                                destination = "/data"
                        }
			vault {
				policies = ["access-cronocide.net"]
			}
			template {
				data = <<EOH
{{with secret "op/vaults/cronocide.net/items/bbbot"}}
{{range $key, $value := .Data}}{{$key}}="{{$value}}"
{{end}}{{end}}
EOH
				destination = "secrets/file.env"
				env = true
			}
			env {
				BIND_PORT="${NOMAD_PORT_http}"
				USE_PRIVATE_API=true
			}
			resources {
				cores = 1
				memory = 512
			}
			restart {
				attempts = 3
				delay    = "30s"
				mode     = "delay"
			}
		}
	}
}
