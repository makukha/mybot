top = '.'
out = 'build'  # don't change this

pkg = 'mybot'


def configure(ctx):
    """
    Configure
    """


def build(ctx):
    """
    Deploy Serverless image
    """
    EXCLUDE = ['**/.DS_Store', '**/__pycache__/**/*', '**/.idea/**/*']

    ctx(rule='docker-compose run --rm default serverless package --package {out} --verbose'.format(out=out),
        source=['requirements.txt', 'serverless.yml', 'credentials']
            + ctx.path.ant_glob(incl='bot/**/*', excl=EXCLUDE),
        target='{pkg}.zip'.format(pkg=pkg),
        name='serverless package')

    ctx(rule='docker-compose run --rm default serverless deploy --package {out} --verbose'.format(out=out),
        source='{pkg}.zip'.format(pkg=pkg),
        depends_on=['serverless package'],
        name='serverless deploy')


def logs(ctx):
    """
    Show logs

    docker-compose run --rm default serverless logs -f default -t
    """
