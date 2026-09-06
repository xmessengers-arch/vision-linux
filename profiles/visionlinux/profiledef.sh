# Vision Linux archiso profile

profile_archiso_version=90
profile_type="baseline"
profile_basedir="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

iso_publisher="Vision Linux <team@visionlinux.dev>"
iso_application="Vision Linux"
iso_version="2026.09.06"
iso_label="VISIONLINUX"
iso_directory="visionlinux"

bootloader="limine"
kernel="linux-lts"
compression="zstd"
