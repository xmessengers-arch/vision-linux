# Vision Linux archiso profile

profile_archiso_version=80
profile_type="baseline"

iso_publisher="Vision Linux <team@visionlinux.dev>"
iso_application="Vision Linux"
iso_version="$(date +%Y.%m.%d)"
iso_label="VISIONLINUX"
iso_directory="visionlinux"
iso_filename="visionlinux-${iso_version}-x86_64.iso"

bootloader="limine"
kernel="linux-lts"
compression="zstd"
