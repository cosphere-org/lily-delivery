
# renames: [
#     {
#         'type': 'file_content',
#         'from': '/monaco/assets',
#         'to': '$VERSION',
#     },
#     {
#         'type': 'file_name',
#         'from': 'dist/index.html',
#         'to': 'dist/index-$VERSION.html',
#     },
#     {
#         'type': 'file_name',
#         'from': 'dist/index.html',
#         'to': 'dist/index-$VERSION.html',
#     },
# ]
from ..describer import Describer


class S3WebsiteDeployer(Describer):

    def deploy(self):
        with self.header('performing a deployment'):
            dist_dir = self.copy_dist()
            self.shuffle_dist(dist_dir)
            self.apply_renames(dist_dir)
            self.upload_to_s3(dist_dir)
            self.refresh_cloudfront()

    def apply_renames(self):
        pass

    def upload_files(self):
        pass

    def refresh_cloudfront(self):
        pass
